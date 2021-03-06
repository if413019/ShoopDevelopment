# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2016, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from __future__ import unicode_literals

from django.utils.encoding import force_text
from jinja2.sandbox import SandboxedEnvironment


class NoLanguageMatches(Exception):
    pass


def render_in_context(context, template_text, html_intent=False):
    """
    Render the given Jinja2 template text in the script context.

    :param context: Script context.
    :type context: shoop.notify.script.Context
    :param template_text: Jinja2 template text.
    :type template_text: str
    :param html_intent: Is the template text intended for HTML output?
                        This currently turns on autoescaping.
    :type html_intent: bool
    :return: Rendered template text
    :rtype: str
    :raises: Whatever Jinja2 might happen to raise
    """
    # TODO: Add some filters/globals into this environment?
    env = SandboxedEnvironment(autoescape=html_intent)
    template = env.from_string(template_text)
    return template.render(context.get_variables())


class Template(object):
    def __init__(self, context, data):
        """
        :param context: Script context
        :type context: shoop.notify.script.Context
        :param data: Template data dictionary
        :type data: dict
        """
        self.context = context
        self.data = data

    def _get_language_data(self, language):
        return self.data.get(force_text(language).lower(), {})

    def has_language(self, language, fields):
        data = self._get_language_data(language)
        return set(data.keys()) >= set(fields)

    def render(self, language, fields):
        """
        Render this template in the given language,
        returning the given fields.

        :param language: Language code (ISO 639-1 or ISO 639-2)
        :type language: str
        :param fields: Desired fields to render.
        :type fields: list[str]
        :return: Dict of field -> rendered content.
        :rtype: dict[str, str]
        """
        data = self._get_language_data(language)

        rendered = {}

        for field in fields:
            field_template = data.get(field)
            if field_template:  # pragma: no branch
                rendered[field] = render_in_context(self.context, field_template, html_intent=False)

        return rendered

    def render_first_match(self, language_preferences, fields):
        # TODO: Document
        for language in language_preferences:
            if self.has_language(language, fields):
                rendered = self.render(language=language, fields=fields)
                rendered["_language"] = language
                return rendered
        raise NoLanguageMatches("No language in template matches any of languages %r for fields %r" % (
            language_preferences, fields
        ))
