# (c) 2012-2013 Continuum Analytics, Inc. / http://continuum.io
# All Rights Reserved
#
# conda is distributed under the terms of the BSD 3-clause license.
# Consult LICENSE.txt or http://opensource.org/licenses/BSD-3-Clause.

from argparse import RawDescriptionHelpFormatter

import common


descr = "Install a list of packages into a specified conda environment."
example = """
examples:
    conda install -n myenv scipy

"""

def configure_parser(sub_parsers):
    p = sub_parsers.add_parser(
        'install',
        formatter_class = RawDescriptionHelpFormatter,
        description = descr,
        help = descr,
        epilog = example,
    )
    common.add_parser_yes(p)
    p.add_argument(
        '-f', "--force",
        action = "store_true",
        help = "force install (even when package already installed), "
               "implies --no-deps",
    )
    p.add_argument(
        "--file",
        action = "store",
        help = "read package versions from FILE",
    )
    p.add_argument(
        "--no-deps",
        action = "store_true",
        help = "do not install dependencies",
    )
    common.add_parser_prefix(p)
    common.add_parser_quiet(p)
    p.add_argument(
        'packages',
        metavar = 'package_version',
        action = "store",
        nargs = '*',
        help = "package versions to install into conda environment",
    )
    p.set_defaults(func=execute)


def execute(args, parser):
    import conda.plan as plan
    from conda.api import get_index


    prefix = common.get_prefix(args)

    if args.force:
        args.no_deps = True

    if args.packages and all(s.endswith('.tar.bz2') for s in args.packages):
        from conda.misc import install_local_packages

        install_local_packages(prefix, args.packages, verbose=not args.quiet)
        return

    if any(s.endswith('.tar.bz2') for s in args.packages):
        raise RuntimeError("mixing specifications and filename not supported")

    if args.file:
        specs = common.specs_from_file(args.file)
    else:
        specs = common.specs_from_args(args.packages)

    common.check_specs(prefix, specs)

    if args.no_deps:
        only_names = set(s.split()[0] for s in specs)
    else:
        only_names = None

    index = get_index()
    actions = plan.install_actions(prefix, index, specs,
                                   force=args.force, only_names=only_names)

    if plan.nothing_to_do(actions):
        print('All requested packages already installed into '
              'environment: %s' % prefix)
        return

    print
    print "Package plan for installation in environment %s:" % prefix
    plan.display_actions(actions, index)

    common.confirm(args)
    plan.execute_actions(actions, index, verbose=not args.quiet)
