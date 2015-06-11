"""Helper functions to run Bladerunner from the command line with argparse."""


import io
import os
import sys
import getpass
import argparse

from bladerunner import Bladerunner, __version__, __release_date__
from bladerunner.formatting import (
    csv_results,
    pretty_results,
    stacked_results,
    DEFAULT_ENCODINGS,
)


def cmdline_entry():
    """argparse's main entry point, performs logic and preformatting."""

    settings, parser = setup_argparse(sys.argv[1:])

    if settings.getHelp:
        raise SystemExit(print_help())

    commands, settings = get_commands(settings)

    get_servers(settings)

    if settings.printFixed and settings.printCSV or not settings.servers:
        parser.print_usage()
        sys.exit(1)

    settings = get_passwords(argparse_unlisted(settings))

    if settings.ssh_key is not None:
        settings.ssh_key = settings.ssh_key[0]
    if settings.username is not None:
        settings.username = settings.username[0]
    if settings.jump_user:
        settings.jump_user = settings.jump_user[0]
    if settings.debug is None:
        settings.debug = True

    options = convert_to_options(settings)

    if settings.printCSV or settings.csv_char != ",":
        options['style'] = -1

    if settings.settingsDebug:
        raise SystemExit(str(options))

    setup_output_file(options)

    return commands, settings.servers, options


def cmdline_exit(results, options):
    """A buffer for selecting the correct output function and exiting.

    Args::

        results: the results dictionary from Bladerunner.run
        options: the options dictionary, uses 'style' and 'stacked' keys
    """

    if options.get("stacked"):
        stacked_results(results, options)
    elif options["style"] < 0 or options["style"] > 3:
        csv_results(results, options)
    else:
        pretty_results(results, options)

    raise SystemExit


def convert_to_options(settings):
    """Converts argparse's namespace into a dictionary. Removes temp keys."""

    return {
        "username": settings.username,
        "jump_user": settings.jump_user,
        "jump_host": settings.jump_host,
        "jump_pass": settings.jump_pass,
        "jump_port": settings.jump_port,
        "debug": settings.debug,
        "delay": settings.delay,
        "output_file": settings.output_file,
        "password": settings.password,
        "second_password": settings.second_password,
        "password_safety": settings.password_safety,
        "ssh_key": settings.ssh_key,
        "style": settings.style,
        "csv_char": settings.csv_char,
        "threads": settings.threads,
        "stacked": settings.stacked,
        "width": settings.printFixed or settings.width,
        "extra_prompts": settings.extra_prompts or [],
        "progressbar": True,
        "port": settings.port,
        "unix_line_endings": settings.unix_line_endings,
        "windows_line_endings": settings.windows_line_endings,
        "timeout": settings.timeout,
        "cmd_timeout": settings.cmd_timeout,
    }


def print_help():
    """Overrides argparses's --help, prints usage only."""

    sys.stdout.write("""{version}
Usage:
  bladerunner [OPTIONS] <COMMAND> <HOST> [HOST] ...
Note:
  <COMMAND> becomes optional if a command --file is used
  <HOST> becomes optional if a --host-file is supplied
Options:
  -a --ascii\t\t\t\tUse ASCII output with normal results (same as --style=1)
  -c --command-timeout=<seconds>\tTimeout between commands (default: 20s)
  -T --connection-timeout=<seconds>\tSpecify the SSH timeout (default: 20s)
  -C --csv\t\t\t\tOutput in CSV format, not grouped by similarity
  -E --csv-separator=<char>\t\tSpecify the seperation character with CSV output
     --debug=[int]\t\t\tDebug to stdout, with optional int of ssh debug level
  -e --end\t\t\t\tSignal the end of flags, useful with --debug or -m ordering
  -f --file=<file>\t\t\tLoad commands from a file
  -F --flat\t\t\t\tOutput results with a flattened/stacked output style
  -x --fixed\t\t\t\tUse a fixed 80 character width for output
  -h --help\t\t\t\tThis help screen
  -H --host-file=<file>\t\t\tLoad hosts from a file
  -j --jumpbox=<host>\t\t\tUse a jumpbox to intermediary the targets
  -P --jumpbox-password=<password>\tSeparate jumpbox password (-P to prompt)
  -J --jumpbox-port=<port>\t\tUse a non-standard SSH port for the jumpbox
  -U --jumpbox-username=<username>\tJumpbox user name (default: {username})
  -m --match=<pattern> [pattern] ...\tMatch additional shell prompts
  -n --no-password\t\t\tNo password prompt
  -N --no-password-check\t\tDon't check if the first login succeeded
  -o --output-file=<file>\t\tAppend the output to a file rather than stdout
  -p --password=<password>\t\tSupply the host password on the command line
  -D --port\t\t\t\tUse a non non-standard SSH port for the target hosts
  -s --second-password=<password>\tSupply a second password (-s to prompt)
  -S --style=<int>\t\t\tOutput style (0=default, 1=ASCII, 2=double, 3=rounded)
  -k --ssh-key=<file>\t\t\tUse a non-default ssh key
  -t --threads=<int>\t\t\tMaximum concurrent threads (default: 100)
  -d --time-delay=<seconds>\t\tAdd a time delay between hosts (default: 0s)
  -X --unix-line-endings\t\tForce the use of \\n for newlines
  -u --username=<username>\t\tUse a different user name (default: {username})
  -v --version\t\t\t\tDisplays version information
  -w --width=<int>\t\t\tSpecify the maximum width to display results in
  -W --windows-line-endings\t\tForce the use of \\r\\n for newlines
""".format(
        version=get_version(),
        username=getpass.getuser(),
    ))


def get_commands(settings):
    """Opens the command file from the settings namespace.

    Args:
        settings: the argparse namespace from the cmdline

    Returns:
        tuple of (commands list, settings namespace)
    """

    if settings.command_file:
        settings.servers.insert(0, settings.command)
        settings.command = None

        try:
            command_list = []
            with open(settings.command_file[0]) as command_file:
                for command_line in command_file:
                    command_line = command_line.strip()
                    if not command_line:
                        continue
                    else:
                        command_list.append(command_line)
            commands = command_list
        except IOError:
            raise SystemExit("Could not open file: {0}".format(
                settings.command_file[0]))
    else:
        commands = [settings.command]

    return commands, settings


def get_servers(settings):
    """Checks to see if a file has been passed as a list of servers."""

    servers = []

    if settings.host_file:
        try:
            with open(settings.host_file[0], "r") as serverfile:
                for line in serverfile.readlines():
                    for server in line.split(" "):
                        if server.strip():
                            servers.append(server.strip())
            settings.servers = servers
        except IOError:
            raise SystemExit("Could not open file: {0}".format(
                settings.host_file[0]))

    if len(settings.servers) == 0 or not settings.servers[0]:
        raise SystemExit(print_help())


def get_passwords(settings):
    """Prompt and sets all passwords."""

    if settings.usePassword is True and not settings.password:
        settings.password = getpass.getpass("Password: ")

    if settings.setsecond_password and not settings.second_password:
        settings.second_password = getpass.getpass("Second password: ")
    elif not settings.second_password:
        settings.second_password = settings.password

    if settings.setjumpbox_password and settings.jump_host:
        settings.jump_pass = getpass.getpass("Jumpbox password: ")
    elif not settings.jump_pass:
        settings.jump_pass = settings.password

    return settings


def get_version():
    """Returns the version of Bladerunner and the python it's running on."""

    return "Bladerunner {ver} on Python {pyv}. Released: {date}".format(
        ver=__version__,
        pyv="{0}.{1}.{2}".format(*sys.version_info[:3]),
        date=__release_date__,
    )


def argparse_unlisted(settings):
    """Argparse likes to nest everything in lists. This undoes that."""

    unlistings = [
        "delay",
        "password",
        "second_password",
        "jump_pass",
        "port",
        "jump_port",
        "debug",
        "output_file",
        "width",
    ]

    for unlisting in unlistings:
        if isinstance(getattr(settings, unlisting), list):
            setattr(settings, unlisting, getattr(settings, unlisting)[0])

    unlist_from_defaults = [
        ("cmd_timeout", 20),
        ("timeout", 20),
        ("threads", 100),
    ]

    for setting, default in unlist_from_defaults:
        if getattr(settings, setting) != default:
            setattr(settings, setting, getattr(settings, setting)[0])

    if settings.printFixed:
        settings.printFixed = 80
    if settings.ascii:
        settings.style = 1
    if settings.csv_char != ',':
        settings.csv_char = settings.csv_char[0][0]

    return settings


def setup_output_file(options):
    """Make sure we can write to the output file if that's being used.

    Args:
        options: original Bladerunner options dictionary

    Returns:
        None, raises SystemExit if the output_file cannot be written
    """

    if options["output_file"]:
        # "touch" the file, ensures we can write the output before execution
        try:
            for enc in DEFAULT_ENCODINGS:
                try:
                    with io.open(options["output_file"], "a", encoding=enc):
                        os.utime(options["output_file"], None)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
                else:
                    break
            else:
                raise SystemExit("Could not create output file: {0}".format(
                    options["output_file"]
                ))
        except IOError as err:
            raise SystemExit("Could not open output file: {0}".format(err))


def setup_argparse(args):
    """Sets up the parser's arguments."""

    parser = argparse.ArgumentParser(
        prog="bladerunner",
        description="A simple way to run quick audits or push changes.",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--ascii",
        "-a",
        dest="ascii",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--command-timeout",
        "-c",
        dest="cmd_timeout",
        metavar="SECONDS",
        nargs=1,
        type=int,
        default=20,
    )

    parser.add_argument(
        "--connection-timeout",
        "-T",
        dest="timeout",
        metavar="SECONDS",
        nargs=1,
        type=int,
        default=20,
    )

    parser.add_argument(
        "--csv",
        "-C",
        dest="printCSV",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--csv-separator",
        "-E",
        dest="csv_char",
        metavar="CHAR",
        nargs=1,
        type=str,
        default=",",
    )

    parser.add_argument(
        "--debug",
        dest="debug",
        metavar="INT",
        nargs="?",
        type=int,
        default=False,
    )

    parser.add_argument(
        "--end",
        "--this-is-the-end",
        "-e",
        dest="jim_morrison",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--file",
        "-f",
        dest="command_file",
        metavar="FILE",
        nargs=1,
        default=False,
    )

    parser.add_argument(
        "--flat",
        "-F",
        dest="stacked",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--fixed",
        "-x",
        dest="printFixed",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--help",
        "-h",
        dest="getHelp",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--host-file",
        "-H",
        dest="host_file",
        metavar="FILE",
        nargs=1,
        default=False,
    )

    parser.add_argument(
        "--jumpbox",
        "-j",
        dest="jump_host",
        metavar="HOST",
    )

    parser.add_argument(
        "--jumpbox-password",
        dest="jump_pass",
        metavar="PASSWORD",
        nargs=1,
        default=False,
    )

    parser.add_argument(
        "--jumpbox-username",
        "-U",
        dest="jump_user",
        metavar="USER",
        nargs=1,
        default=False,
    )

    parser.add_argument(
        "--jumpbox-port",
        "-J",
        dest="jump_port",
        metavar="PORT",
        nargs=1,
        type=int,
        default=22,
    )

    parser.add_argument(
        "--match",
        "-m",
        dest="extra_prompts",
        metavar="PATTERN",
        nargs="+",
    )

    parser.add_argument(
        "--no-password",
        "-n",
        dest="usePassword",
        action="store_false",
        default=True,
    )

    parser.add_argument(
        "--output-file",
        "-o",
        dest="output_file",
        metavar="FILE",
        nargs=1,
        default=False,
    )

    parser.add_argument(
        "--password",
        "-p",
        dest="password",
        metavar="PASSWORD",
        nargs=1,
    )

    parser.add_argument(
        "--port",
        "-D",
        dest="port",
        metavar="PORT",
        nargs=1,
        type=int,
        default=22
    )

    parser.add_argument(
        "-P",
        dest="setjumpbox_password",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-s",
        dest="setsecond_password",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--second-password",
        dest="second_password",
        metavar="PASSWORD",
        nargs=1,
    )

    parser.add_argument(
        "--settings",
        dest="settingsDebug",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--ssh-key",
        "-k",
        dest="ssh_key",
        metavar="FILE",
        nargs=1,
    )

    parser.add_argument(
        "--style",
        "-S",
        dest="style",
        metavar="INT",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--time-delay",
        "-d",
        dest="delay",
        metavar="SECONDS",
        nargs=1,
        type=float,
        default=0,
    )

    parser.add_argument(
        "--threads",
        "-t",
        dest="threads",
        metavar="INT",
        nargs=1,
        type=int,
        default=100,
    )

    parser.add_argument(
        "--username",
        "-u",
        dest="username",
        metavar="USER",
        nargs=1,
    )

    parser.add_argument(
        "--unix-line-endings",
        "-X",
        dest="unix_line_endings",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--no-password-check",
        "-N",
        dest="password_safety",
        action="store_false",
        default=True,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=get_version(),
    )

    parser.add_argument(
        "--windows-line-endings",
        "-W",
        dest="windows_line_endings",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--width",
        "-w",
        metavar="INT",
        dest="width",
        nargs=1,
        type=int,
        default=False,
    )

    parser.add_argument(
        dest="command",
        metavar="COMMAND",
        nargs="?",
    )

    parser.add_argument(
        dest="servers",
        metavar="HOST",
        nargs=argparse.REMAINDER,
    )

    settings = parser.parse_args(args)
    return (settings, parser)


def main():
    """Main run loop, except KeyboardInterrupts."""

    try:
        commands, servers, options = cmdline_entry()
        results = Bladerunner(options).run(commands, servers)
        cmdline_exit(results, options)
    except KeyboardInterrupt:
        raise SystemExit("interrupted")
