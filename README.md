Health:
Travis [![Build Status](https://travis-ci.org/e3krisztian/bead.svg?branch=master)](https://travis-ci.org/e3krisztian/bead)
AppVeyor [![Build Status](https://ci.appveyor.com/api/projects/status/github/e3krisztian/bead?branch=master&svg=true)](https://ci.appveyor.com/project/e3krisztian/bead)

    B-E-+
     \ \ \
      +-A-D

# BEAD


BEAD is a format for freezing and storing computations while `bead` is a tool that helps
capturing and managing computations in BEAD formats.


## Concept

Given a discrete computation of the form

    output = function(*inputs)

a BEAD captures all three named parts:

- `output` - *data files* (results of the computation)
- `function` - *source code files*, that when run hopefully compute `output` from `inputs`
- `inputs` - are other BEADs' `output` and thus stored as *references to* those *BEADs*

As a special case pure data can be thought of as *constant computation*
having only output but neither inputs nor source code.

A BEAD has some other metadata - notably it has a `kind` property which is shared by
different versions of the conceptually same computation (input or function may be updated/improved)
and a timestamp when the computation was frozen.

The `kind` and timestamp properties enable a meaningful `update` operation on inputs.

New computations get a new, universally unique `kind` (technically an uuid).


## Status

### Used in production for 2 years now, there are 100+ frozen computations

Although most of the important stuff is implemented, there are still some raw edges.

Documentation for the tool is mostly the command line help.

The `doc` directory has concept descriptions, maybe some use cases,
but there are also design fragments - you might be mislead by them as they
are nor describing the current situations nor are they showing the future.
FIXME: clean up documentation.


## Install instructions

Ensure you have Python 3.6+ installed.

Run `make executables` to create the `bead` tool:

```
$ python build.py
```

This generates one-file executables for unix, mac, and windows in the `executables` directory:
- `bead` unix & mac
- `bead.cmd` windows

Move/copy the `bead` binary for your platform to some directory on your `PATH`.

E.g.

```
$ cp executables/bead ~/.local/bin
```

If you test it, please give [feedback](../../issues) on
- general usability
- misleading/unclear help (currently: command line help)
- what is missing (I know about documentation)
- what is not working as you would expect

Any other nuisance reported - however minor you think it be - is important and welcome!

Thank you for your interest!


## TODOs

Updated by script ([./ci](https://github.com/e3krisztian/bead/blob/master/ci)), text in this section and afterwards will be overwritten

- [FIXME: Archive.is_valid is too costly for a property](https://github.com/e3krisztian/bead/blob/master/bead/archive.py#L68)
- [FIXME: die with message when directory already exists](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L53)
- [FIXME: rename Bead.timestamp* to .freeze_time*](https://github.com/e3krisztian/bead/blob/master/bead/bead.py#L24)
- [FIXME: robot: environment file should be built by a function in environment](https://github.com/e3krisztian/bead/blob/master/bead_cli/test_robot.py#L21)
- [FIXME: test_archive.given_a_bead is fragile and yields an invalid BEAD](https://github.com/e3krisztian/bead/blob/master/bead/test_archive.py#L41)
- [TODO: add tests for timestamps, parse_iso8601, parse_timedelta](https://github.com/e3krisztian/bead/blob/master/bead/tech/timestamp.py#L229)
- [TODO: ask the user to report the exception?!](https://github.com/e3krisztian/bead/blob/master/bead_cli/main.py#L107)
- [TODO: Box: support user maintained directory hierarchy](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L91)
- [TODO: log/report problem](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L146)
- [TODO: update: assert there is no other argument](https://github.com/e3krisztian/bead/blob/master/bead_cli/input.py#L111)
- [TODO: use a template and render it with passing in all data](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L230)
- [XXX: cli parsing: revisit when python 2.x no longer supported](https://github.com/e3krisztian/bead/blob/master/bead_cli/cmdparse.py#L80)
- [XXX: directory itself might be a pattern - is it OK?](https://github.com/e3krisztian/bead/blob/master/bead/box.py#L135)
- [XXX: introspect parameter names, default values, annotations?](https://github.com/e3krisztian/bead/blob/master/bead_cli/cmdparse.py#L115)
- [XXX: list command: use tabulate?](https://github.com/e3krisztian/bead/blob/master/bead_cli/box.py#L51)
- [XXX: try to load smaller inputs?](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L160)
- [XXX: (usability) save - support saving directly to a directory outside of workspace](https://github.com/e3krisztian/bead/blob/master/bead_cli/workspace.py#L90)
