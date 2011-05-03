# -*- coding: utf-8 -*-
# <Lettuce - Behaviour Driven Development for python>
# Copyright (C) <2010-2011>  Gabriel Falcão <gabriel@nacaolivre.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERsteps.pyCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import os
import string
import sys
import unicodedata
from datetime import datetime
from lettuce import core
from lettuce.terrain import after

failed_scenarios = []
scenarios_and_its_fails = {}

_valid_filename_chars = "-_.()%s%s" % (string.ascii_letters, string.digits)

def _remove_disallowed_filename_chars(filename):
    """return string as valid filename"""
    cleaned_filename = filename.replace(" ","_")
    cleaned_filename = unicodedata.normalize('NFKD', cleaned_filename).encode('ASCII', 'ignore')
    return ''.join(c for c in cleaned_filename if c in _valid_filename_chars)


def print_error_with_exception(s,exception):
    """prints string s to terminal in red with trace of exception"""
    print_error(s)
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback)

def _get_time_now_for_dir():
    now = datetime.now()
    datedir = now.strftime("%Y-%m-%d-%H-%M")
    path = "/tmp/lyst-lettuce-error-screenshots/"+ datedir +"/"
    return path

_SCREENSHOT_ERROR_PATH = _get_time_now_for_dir()

def _mkdir_path(path):
    """makes a directory, does nothing if dir exists"""
    if not os.access(path, os.F_OK):
        os.makedirs(path)

def _write_to_file(s, filename):
    """opens filename and writes string s to it"""
    if not s:
        return
    if not filename:
        return
    try:
        f = codecs.open(filename, "w", "utf-8-sig")
        try:
            f.write(s)
        except Exception, e:
            print_error_with_exception("Exception writing to file %s : %s" % (filename,e), e)
        finally:
            f.close()
    except Exception, e:
        print_error_with_exception("Exception opening file %s : %s" % (filename,e), e)

def wrt(string):
    sys.stdout.write(string)
    sys.stdout.flush()

@after.each_step
def print_scenario_ran(step):
    if not step.failed:
        wrt(".")
    elif step.failed:
        if step.scenario not in failed_scenarios:
            path = _SCREENSHOT_ERROR_PATH + \
                step.scenario.name + "/" + \
                step.scenario.feature.name + "/"
            _mkdir_path(path)
            filename_base = path + _remove_disallowed_filename_chars(step.sentence)
            filename_pic = filename_base + ".png"
            filename_src = filename_base + ".html"
            _write_to_file(world.browser.get_page_source(), filename_src)
            success = world.browser.get_screenshot_as_file(filename_pic)
            scenarios_and_its_fails[step.scenario] = """Step: %s
Scenario: %s
Feature: %s
Feature File: %s
Current URL: %s
Screenshot URL: http://jenkins.lystit.com%s
HTML URL: http://jenkins.lystit.com%s
Traceback:
%s
""" % (step.sentence,
       step.scenario.name,
       step.scenario.feature_name,
       step.scenario.with_file,
       world.browser.current_url,
       filename_src,
       filename_pic,
       step.why)
            failed_scenarios.append(step.scenario)

        if isinstance(step.why.exception, AssertionError):
            wrt("F")
        else:
            wrt("E")

@after.all
def print_end(total):
    if total.scenarios_passed < total.scenarios_ran:
        wrt("\n")
        wrt("\n")
        for scenario in failed_scenarios:
            reason = scenarios_and_its_fails[scenario]
            wrt(reason.traceback)

    wrt("\n")
    word = total.features_ran > 1 and "features" or "feature"
    wrt("%d %s (%d passed)\n" % (
        total.features_ran,
        word,
        total.features_passed
        )
    )

    word = total.scenarios_ran > 1 and "scenarios" or "scenario"
    wrt("%d %s (%d passed)\n" % (
        total.scenarios_ran,
        word,
        total.scenarios_passed
        )
    )

    steps_details = []
    for kind in ("failed","skipped",  "undefined"):
        attr = 'steps_%s' % kind
        stotal = getattr(total, attr)
        if stotal:
            steps_details.append(
                "%d %s" % (stotal, kind)
            )

    steps_details.append("%d passed" % total.steps_passed)
    word = total.steps > 1 and "steps" or "step"
    wrt("%d %s (%s)\n" % (
        total.steps,
        word,
        ", ".join(steps_details)
        )
    )

def print_no_features_found(where):
    where = core.fs.relpath(where)
    if not where.startswith(os.sep):
        where = '.%s%s' % (os.sep, where)

    wrt('Oops!\n')
    wrt(
        'could not find features at '
        '%s\n' % where
    )
