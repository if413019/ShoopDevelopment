# -*- coding: utf-8 -*-
import six

from shoop.xtheme.layout import Layout, LayoutCell
from shoop.xtheme.plugins.text import TextPlugin
from shoop.xtheme.rendering import get_view_config, render_placeholder
from shoop.xtheme.testing import override_current_theme_class
from shoop_tests.utils import printable_gibberish
from shoop_tests.xtheme.utils import (
    close_enough, get_request, get_test_template_bits, plugin_override
)


def test_layout_serialization():
    with plugin_override():
        l = Layout("test")
        l.begin_column({"md": 8})
        l.add_plugin("text", {"text": "yes"})
        serialized = l.serialize()
        expected = {
            'name': "test",
            'rows': [
                {
                    'cells': [
                        {'config': {'text': 'yes'}, 'plugin': 'text', 'sizes': {"md": 8}}
                    ]
                }
            ]
        }
        assert serialized == expected
        assert Layout.unserialize(serialized).serialize() == expected


def test_layout_rendering(rf):
    request = get_request(edit=False)
    with override_current_theme_class(None):
        with plugin_override():
            (template, layout, gibberish, ctx) = get_test_template_bits(request)

            result = six.text_type(render_placeholder(ctx, "test", layout, "test"))
            expect = """
            <div class="xt-ph" id="xt-ph-test">
            <div class="row xt-ph-row">
            <div class="col-md-12 hidden-xs xt-ph-cell"><p>%s</p></div>
            </div>
            </div>
            """ % gibberish
            assert close_enough(result, expect)


def test_layout_edit_render():
    request = get_request(edit=True)
    with override_current_theme_class(None):
        with plugin_override():
            (template, layout, gibberish, ctx) = get_test_template_bits(request)
            result = six.text_type(render_placeholder(ctx, "test", layout, "test"))
            # Look for evidence of editing:
            assert "xt-ph-edit" in result
            assert "data-xt-placeholder-name" in result
            assert "data-xt-row" in result
            assert "data-xt-cell" in result


def test_view_config_caches_into_context(rf):
    # This is a silly test...
    request = get_request(edit=False)
    with override_current_theme_class(None):
        (template, layout, gibberish, ctx) = get_test_template_bits(request)
        cfg1 = get_view_config(ctx)
        cfg2 = get_view_config(ctx)
        assert cfg1 is cfg2
        (template, layout, gibberish, ctx) = get_test_template_bits(request, False)
        cfg1 = get_view_config(ctx)
        cfg2 = get_view_config(ctx)
        assert cfg1 is cfg2


def test_missing_plugin_render():
    plugin_id = printable_gibberish()
    cell = LayoutCell(plugin_identifier=plugin_id)
    assert not cell.plugin_class
    assert not cell.instantiate_plugin()
    assert ("%s?" % plugin_id) in cell.render(None)  # Should render a "whut?" comment


def test_null_cell_render():
    cell = LayoutCell(None)
    assert not cell.plugin_class
    assert not cell.instantiate_plugin()
    assert not cell.render(None)  # Should render nothing whatsoever!


def test_plugin_naming():
    with plugin_override():
        cell = LayoutCell(TextPlugin.identifier)
        assert cell.plugin_name == TextPlugin.name


def test_layout_api():
    l = Layout("test")
    l.begin_column({"md": 8})
    px0y0 = l.add_plugin("text", {"text": "yes"})
    l.begin_column({"md": 4})
    px1y0 = l.add_plugin("text", {"text": "no"})
    assert len(l) == 1
    assert len(l.rows[0]) == 2
    assert not l.delete_cell(x=0, y=1)  # nonexistent row
    assert l.get_cell(0, 0) == px0y0
    assert l.get_cell(1, 0) == px1y0
    assert not l.get_cell(2, 0)
    assert not l.get_cell(0, 1)
    l.begin_row()
    assert len(l) == 2
    assert len(l.rows[1]) == 0
    l.begin_column()
    assert len(l.rows[1]) == 1
    assert l.delete_cell(x=0, y=1)  # existent cell
    assert not l.delete_cell(x=0, y=1)  # cell existent no more
    assert l.delete_row(1)  # existent row
    assert len(l) == 1
    assert not l.delete_row(1)  # nonexistent row
    l.insert_row(0).add_cell()  # insert a cellful row in first place
    assert len(l) == 2 and list(map(len, l.rows)) == [1, 2]
    l.insert_row(1)  # insert an empty row in second place
    assert len(l) == 3 and list(map(len, l.rows)) == [1, 0, 2]
    assert not l.insert_row(-1)  # that's silly!
