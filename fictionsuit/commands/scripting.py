from __future__ import annotations

import glob
import ntpath
import os
import re
import string
import traceback

from ..api_wrap.bluesky import BlueskyClientFactory

from .failure import CommandFailure

from ..api_wrap.openai import ChatFactory, ChatInstance
from ..core.fictionscript import (
    ExpressionMessage,
    FictionScript,
    Scope,
    ScriptLineMessage,
)
from ..core.user_message import UserMessage
from .command_group import (
    CommandGroup,
    command_split,
    slow_command,
)

COMMA_ESCAPE = "``COM"
COMMA_ESCAPE_B = "```COM"

# This file is doing way too many things


def escape_commas(command):
    command.escape_commas = True
    return command


def no_preprocessing_after(sequence: str, unless: str = None):
    """Marks a command, telling the preprocessor not to modify any of the text after the given sequence."""

    def decorator(command):
        command.no_preprocessing_after = sequence
        command.unless = unless
        return command

    return decorator


def lsnap(string: str, delimiter: str) -> tuple[str, str]:
    """Breaks a string into two parts, splitting at the first instance of the delimiter.
    The delimiter (and any whitespace surrounding it) is not included in either part.
    If the delimiter is not found, the first part is the entire string, and the second part is the empty string.
    """
    split = string.split(delimiter, maxsplit=1)
    if len(split) < 2:
        return (string, "")
    return (split[0].rstrip(), split[1].lstrip())


def rsnap(string: str, delimiter: str) -> tuple[str, str]:
    """Breaks a string into two parts, splitting at the last instance of the delimiter.
    The delimiter (and any whitespace surrounding it) is not included in either part.
    If the delimiter is not found, the second part is the entire string, and the second part is the empty string.
    """
    split = string.rsplit(delimiter, maxsplit=1)
    if len(split) < 2:
        return ("", string)
    return (split[0].rstrip(), split[1].lstrip())


class VarFormatter(string.Formatter):
    def get_field(self, field_name, args, kwargs):
        return super().get_field(
            " > ".join(x.strip() for x in field_name.split(".")), args, kwargs
        )


class Scripting(CommandGroup):
    """This command group contains the fundamental commands necessary for scripting.
    Many of these commands have special syntax, though they can also be called normally.
    """

    def __init__(self, command_groups: list[CommandGroup]):
        self.command_groups = command_groups + [self]
        self.base = Scope()  # TODO: save and load scopes?
        self.vars = self.base
        # TODO: Concurrency -- probably easiest to just put every user in their own scope
        # TODO: add a more general preprocessor outside of Scripting for parsing scripts
        # from a nicer syntax down into runnable commands
        # TODO: maybe add config options for folders instead of just hard-coding things...
        self.vars["fic"] = Scope(name="fic", parent=self.vars)
        self.load_scripts("fictionsuit/fic", self.vars["fic"])
        self.load_scripts("fictionsuit/.fic", self.vars["fic"])
        self.vars["fic"]["chat"] = ChatFactory()
        self.vars["fic"]["bsky"] = BlueskyClientFactory()

        self.evaluators = {}
        self.escape_commas = []

        self.var_formatter = VarFormatter()

        for group in self.command_groups:
            cmds = group.get_commands()
            for cmd in cmds:
                if hasattr(cmds[cmd], "no_preprocessing_after"):
                    self.evaluators[cmd] = (
                        cmds[cmd].no_preprocessing_after,
                        cmds[cmd].unless,
                    )
                if hasattr(cmds[cmd], "escape_commas"):
                    self.escape_commas.append(cmd)

    async def intercept_content(self, content: str) -> str | CommandFailure:
        """This method modifies incoming commands, converting fictionscript syntax into
        normal commands.
        The syntax of these commands is described in the docstrings of the commands themselves,
        as well as in `fic/README.md`.
        """
        # print(f"Begin Interception: [{content}]")
        # print(self.vars.inspect())

        (cmd, args) = command_split(content)

        if cmd is None:
            return content

        if cmd[0] == "#":
            return content  # Comment; do nothing

        def handle_scope_access(content: str, cmd: str, args: str) -> str:
            # print(f"Handle scope access: [{content}]")
            # print(f"cmd: [{cmd}]")
            # print(f"args: [{args}]")
            n = 1
            if cmd is None:
                return content
            if cmd[0] not in ".?":
                return content
            if "=" in content:
                if "." not in content[1 : content.index("=")]:
                    expansion = "var"
                else:
                    expansion = "insert"
            else:
                content = content.strip()
                if content == f".":
                    expansion = "where"
                elif content == f"?":
                    expansion = "inspect where"
                elif content == f"??":
                    n = 2
                    expansion = "dump where"
                else:
                    if content.endswith("??"):
                        expansion = "dump retrieve"
                        cmd = cmd[1:] + args
                        cmd = cmd[:-2].rstrip()
                        args = ""
                        n = 0
                    elif content.endswith("?"):
                        expansion = "inspect retrieve"
                        cmd = cmd[1:] + args
                        cmd = cmd[:-1].rstrip()
                        args = ""
                        n = 0
                    else:
                        expansion = "retrieve"
            x = " ".join([expansion, cmd[n:], args])
            # print(f"Scope access expansion: [{x}]")
            return x

        content = handle_scope_access(content, cmd, args)

        (cmd, args) = command_split(content)

        unchanged = ""

        if cmd == "...":
            content = f"silently {content[3:]}"

        if cmd in self.evaluators:
            after = self.evaluators[cmd][0]
            unless = self.evaluators[cmd][1]
            if after == "":
                split = ["", content]
            else:
                split = None
                try:
                    unless_index = content.index(unless)
                except:
                    unless_index = -1
                if unless_index != -1:
                    try:
                        after_index = content.index(after)
                    except:
                        after_index = -1
                    if unless_index < after_index:
                        split = [content]
                if split is None:
                    split = content.split(after, maxsplit=1)
            if len(split) > 1:
                unchanged = f"{after} {split[1].lstrip()}"
                if unchanged[0] != "\n":
                    unchanged = unchanged.lstrip()
            content = split[0].rstrip()

        if cmd in self.escape_commas:
            content = content.replace("\\,", COMMA_ESCAPE)
            content = content.replace(",", COMMA_ESCAPE_B)
        try:
            content = self.var_formatter.format(content, **self.vars.get_vars())
            content = content.replace("}", "}}")
            content = content.replace("{", "{{")
        except KeyError as k:
            return CommandFailure(f"No such variable: {k}")
        if cmd in self.escape_commas:
            content = content.replace(",", COMMA_ESCAPE)
            content = content.replace(COMMA_ESCAPE_B, ",")

        content = content.replace("\\n", "\n")
        content = f"{content} {unchanged}".strip()

        # print(f"End Interception: [{content}]")
        return content

    def load_scripts(self, directory_name, scope: Scope):
        """Load all .fic scripts from a directory into a scope."""
        for file in glob.glob(os.path.join(directory_name, "*.fic")):
            var_name = ntpath.basename(file)
            script = FictionScript.from_file(file, var_name)
            if var_name.endswith(".fic"):
                var_name = var_name[:-4].replace("_", " ").lower()
            scope[var_name] = script

    async def cmd_drop(self, message: UserMessage, args: str):
        """Drop a variable from the current scope.
        Usage:
        `drop {variable name}`"""
        try:
            del self.vars.vars[args]
        except KeyError:
            return CommandFailure(f"No such variable: {args}")

    @no_preprocessing_after(":")
    @slow_command
    async def cmd_for(self, message: UserMessage, args: str):
        """Iterate over a scope's contents.
        Usage:
        `for {variable} : {scope} \n {command}`
        """
        (loop_variable, args) = lsnap(args, ":")
        if loop_variable == "" or args == "":
            return CommandFailure("Usage: `for {variable} : {scope} \n {command}`")
        (source_scope, command) = lsnap(args, "\n")
        if source_scope == "" or command == "":
            return CommandFailure("Usage: `for {variable} : {scope} \n {command}`")

        source_scope = await self._evaluate(
            message, source_scope, "for loop source scope"
        )

        if isinstance(source_scope, CommandFailure):
            return CommandFailure(
                f"Failed evaluating source_scope of for loop.\n{source_scope}"
            )

        if not isinstance(source_scope, Scope):
            return CommandFailure(f"Expected a scope, got `{source_scope}`")

        execution_scope = Scope(
            parent=source_scope, name=f"for {loop_variable} execution context"
        )
        execution_scope["results"] = Scope(
            parent=execution_scope, name=f"for {loop_variable}"
        )

        script = None
        if "\n" in command:
            script = FictionScript(command.split("\n"), name="_temp_for")

        for variable_name in source_scope.vars:
            execution_scope[loop_variable] = source_scope[variable_name]
            execution_scope["name"] = variable_name
            if script is None:
                result = await self._evaluate(
                    message, command, "for loop command", execution_scope
                )
            else:
                result = await self._fic(message, "", script, execution_scope)
            if isinstance(result, CommandFailure):
                return CommandFailure(f"Failed evaluating for loop command.\n{result}")

        return execution_scope["results"]

    async def cmd_where(self, message: UserMessage, args: str) -> str:
        """Returns the current scope.
        Usage:
        `.` (shorthand)
        `where`"""
        return self.vars

    async def cmd_scope(self, message: UserMessage, args: str) -> Scope:
        if args != "":
            self.vars[args] = Scope(parent=self.vars, name=args)
            return
        return Scope(parent=self.vars)

    async def cmd_into(self, message: UserMessage, args: str) -> Scope:
        """Enters a scope, creating the scope if it does not already exist.
        Fails if the variable exists but is not a scope.
        Usage:
        `into {target scope}`"""
        vars = self.vars.get_vars()
        if args not in self.vars:
            vars[args] = Scope(parent=self.vars, name=args)
        target = vars[args]
        if not isinstance(target, Scope):
            return CommandFailure(f"Variable `{args}` is not a scope.")
        self.vars = target

    async def cmd_out(self, message: UserMessage, args: str) -> None | CommandFailure:
        """Exits the current scope, moving to its parent scope.
        Fails if the current scope has no parent.
        Usage:
        `out`"""
        if self.vars.parent is None:
            return CommandFailure("Cannot exit scope, as there is no parent scope.")
        self._return_to_scope(self.vars.parent)

    async def cmd_base(self, message: UserMessage, args: str) -> None:
        """Enters the base scope.
        Usage:
        `base`"""
        self._return_to_scope(self.base)

    async def cmd_outer(self, message: UserMessage, args: str):
        """Retrieve the value of a variable from the parent scope.
        Fails if the current scope has no parent.
        Usage:
        `outer {variable name}`"""
        if args == "":
            if self.vars.parent is None:
                return CommandFailure(
                    "There is no outer scope -- this is the base scope."
                )
            return self.vars.parent
        return self.vars.parent[args]

    @no_preprocessing_after("")
    async def cmd_inspect(self, message: UserMessage, args: str):
        """Call the `sm_inspect` scripting method of a variable in the current scope.
        Fails if the variable does not have such a method.
        A `sm_inspect` method should provide a concise representation of the variable's state.
        Usage:
        `inspect {variable name}`
        `. {variable name} ?` (shorthand)
        `<variable name?>` (shorthand)"""
        result = await self._evaluate(message, args, "inspection")
        if hasattr(result, "sm_inspect"):
            try:
                return await result.sm_inspect("")
            except Exception as ex:
                return CommandFailure(
                    f"Inspection failed: {ex}\n{traceback.format_exc()}"
                )
        if isinstance(result, str):
            return f'str("{result}")'
        return CommandFailure(f"Cannot inspect {result}")

    @no_preprocessing_after("")
    async def cmd_dump(self, message: UserMessage, args: str):
        """Call the `sm_dump` scripting method of a variable in the current scope.
        Fails if the variable does not have such a method.
        A `sm_dump` method should provide a verbose representation of the variable's state.
        Usage:
        `dump {variable name}`
        `. {variable name} ??` (shorthand)
        `<variable name??>` (shorthand)"""
        result = await self._evaluate(message, args, "dump")
        if hasattr(result, "sm_dump"):
            try:
                return await result.sm_dump("")
            except Exception as ex:
                return CommandFailure(f"Dump failed: {ex}\n{traceback.format_exc()}")
        if isinstance(result, str):
            return f'str("{result}")'
        return CommandFailure(f"Cannot dump {result}")

    thenfinder = re.compile("\s+then\s+")
    elsefinder = re.compile("\s+else\s+")

    @no_preprocessing_after("")
    @slow_command
    async def cmd_if(self, message: UserMessage, args: str):
        """Evaluates a condition and executes a block of code if the condition is true.
        Optionally, another block of code can be provided that will be executed if the condition is false.
        Fails if the condition does not return a boolean value.
        Usage:
        `if {condition} then {then block}`
        `if {condition} then {then block} else {else block}`
        The then and else blocks can be multiple lines."""
        cond_then_split = [
            x.strip() for x in Scripting.thenfinder.split(args, maxsplit=1)
        ]
        if len(cond_then_split) < 2:
            return CommandFailure("An `if` needs a `then`.")
        cond = cond_then_split[0]
        then_else_split = [
            x.strip()
            for x in Scripting.elsefinder.split(cond_then_split[1], maxsplit=1)
        ]
        then = then_else_split[0]
        if len(then_else_split) < 2:
            _else = None
        else:
            _else = then_else_split[1]

        cond_result = await self._evaluate(message, cond, "if condition")

        if isinstance(cond_result, CommandFailure):
            return CommandFailure(f"Failed while evaluating condition:\n{cond_result}")

        if not isinstance(cond_result, bool):
            return CommandFailure(
                f"If condition should be a bool, but was `{cond_result}`."
            )

        if cond_result:
            block = then
            clause = "then"
        elif _else is not None:
            block = _else
            clause = "else"
        else:
            return

        script = None
        if "\n" in block:
            script = FictionScript(block.split("\n"), name=f"_temp_if_{clause}")

        scope = Scope(parent=self.vars, name=f"_temp_if_{clause}")

        if script is not None:
            return await self._fic(message, "", script, scope)
        else:
            return await self._evaluate(message, block, f"{clause} clause", scope)

    @no_preprocessing_after("")
    @slow_command
    async def cmd_while(self, message: UserMessage, args: str):
        """Repeatedly evaluates a condition and executes a block of code until the condition is false.
        Fails if the condition ever returns a non-boolean value.
        Usage:
        `while {condition} \n {body}`"""
        cond_do_split = [x.strip() for x in args.split("\n", maxsplit=1)]
        if len(cond_do_split) < 2:
            return CommandFailure("A while loop needs a body.")
        cond = cond_do_split[0]
        body = cond_do_split[1]

        while True:
            cond_result = await self._evaluate(message, cond, "while condition")

            if isinstance(cond_result, CommandFailure):
                return CommandFailure(
                    f"Failed while evaluating condition:\n{cond_result}"
                )

            if not isinstance(cond_result, bool):
                return CommandFailure(
                    f"While condition should be a bool, but was `{cond_result}`."
                )

            if not cond_result:
                return

            result = await self._evaluate(message, body, "body of while loop")
            if isinstance(result, CommandFailure):
                return CommandFailure(f"Failed in body of while loop:\n{result}")

    async def cmd_fail(self, message: UserMessage, args: str):
        """Return a CommandFailure.
        An explanation can be provided. This is not required but it is strongly recommended.
        Usage:
        `fail {reason}`
        `fail` (returns a CommandFailure with "No explanation." as the message)"""
        if args == "":
            args = "No explanation."
        return CommandFailure(args)

    @no_preprocessing_after("")
    async def cmd_silently(self, message: UserMessage, args: str):
        """Attempt to evaluate a command. Returns nothing, even if the command fails.
        Usage:
        `silently {command}`"""
        await self._evaluate(message, args, "silenced evaluation")

    async def cmd_retrieve(self, message: UserMessage, args: str):
        """Retrieve a value from within a scope, or from scopes within scopes.
        This command can also be used to index into any variable that supports indexing.
        The index will be parsed as an integer if possible.
        Usage:
        `retrieve {variable name}`
        `. {variable name}` (shorthand)
        `. {scope name} . {variable within that scope}`
        `. {index} @ {variable that supports indexing}`"""
        index = None
        index_split = [x.strip() for x in args.split("@", maxsplit=1)]
        if len(index_split) == 2:
            try:
                index = int(index_split[0])
            except ValueError:
                index = index_split[0]
            args = index_split[1]

        scope = self.vars
        while len(args) > 0 and args[0] == "." and scope.parent is not None:
            args = args[1:].lstrip()
            scope = scope.parent

        split = [x.strip() for x in args.split(".") if x != ""]

        result = scope
        for name in split:
            if name in result:
                result = result[name]
            else:
                return CommandFailure(f'"{name}" not found.')

        if index is not None:
            try:
                return result[index]
            except TypeError as err:
                return CommandFailure(f'Cannot index into "{result}":\n{err}')
            except IndexError as err:
                return CommandFailure(f"Failed to access index {index}:\n{err}")

        return result

    @no_preprocessing_after("")
    async def cmd_not(self, message: UserMessage, args: str):
        """Evaluate an expression, and return its negation.
        Returns a CommandFailure if the expression does not return a boolean.
        Usage:
        `not {expression}`"""
        result = await self._evaluate(message, args, "negation")
        if isinstance(result, CommandFailure):
            return CommandFailure(f"Failed while evaluating expression:\n{result}")
        if not isinstance(result, bool):
            return CommandFailure(
                f'Cannot negate "{result}", because it is not a boolean.'
            )
        return not result

    @no_preprocessing_after("=", unless=":=")
    async def cmd_insert(self, message: UserMessage, args: str):
        """Evaluate an expression and store its return value in a variable within a scope within the current scope.
        If ":=" is used instead of "=", the expression will be treated as a string literal instead of being evaluated.
        Usage:
        `insert {scope name} . {variable within that scope} = {expression}`
        `. {scope name} . {variable within that scope} = {expression}` (shorthand)
        `. {scope} . {variable} := {string literal}`"""
        echo = False
        if ":=" in args:
            split = [x.strip() for x in args.split(":=", maxsplit=1)]
            echo = True
        else:
            split = [x.strip() for x in args.split("=", maxsplit=1)]

        retrieval = split[0]
        if len(split) < 2:
            return CommandFailure("No expression to insert.")
        insertion = split[1]

        scope = self.vars
        while len(retrieval) > 0 and retrieval[0] == "." and scope.parent is not None:
            retrieval = retrieval[1:].lstrip()
            scope = scope.parent

        retrieval_split = [x.strip() for x in retrieval.split(".")]
        if len(retrieval_split) == 1:
            if retrieval_split[0] == "":
                return CommandFailure("No insert destination.")

        for name in retrieval_split[:-1]:
            if name in scope:
                scope = scope[name]
            else:
                return CommandFailure(f'"{name}" not found.')

        original_scope = self.vars
        self.vars = scope
        try:
            if echo:
                result = await self.cmd_var(
                    message, f"{retrieval_split[-1]} := {insertion}"
                )
            else:
                result = await self.cmd_var(
                    message, f"{retrieval_split[-1]} = {insertion}"
                )
            return result
        finally:
            self._return_to_scope(original_scope)

    def _return_to_scope(self, scope: Scope) -> None:
        self.vars = scope
        # gc.collect()

    @no_preprocessing_after("")
    async def cmd_fails(self, message: UserMessage, args: str):
        """Evaluate an expression. Returns True if the expression returns a CommandFailure, False otherwise.
        Usage:
        `fails {expression}`"""
        result = await self._evaluate(message, args, "failure check")
        return isinstance(result, CommandFailure)

    @no_preprocessing_after("=", unless=":=")
    @slow_command
    async def cmd_arg(self, message: UserMessage, args: str) -> None | CommandFailure:
        """This command is primarily for use in fictionscripts, to define required inputs.
        If a variable with the argument's name exists, this command does nothing. If no such variable exists,
        this command will fail unless a default value is provided.
        In a script, args with no default values cannot follow an argument with a default value.
        If an argument starts with ":", the value provided for the argument will be interpreted as a string literal.
        Otherwise, the value will be evaluated as an expression.
        Usage:
        `arg {name of argument}`
        `arg {name of argument} = {expression that returns a default value}`
        `arg {name of argument} := {default value, as a literal string}`
        `arg :{name}` (defines a string argument with no default value)"""
        defaulting = "=" in args
        if defaulting:
            self.vars._has_defaulting_args = True
        if not defaulting and self.vars._has_defaulting_args:
            return CommandFailure(
                "Arguments without defaults must precede arguments with defaults."
            )
        if args.startswith(":"):
            args = args[1:]
        echo = ":=" in args
        if echo:
            arg_name = args.split(":=", maxsplit=1)[0].strip()
        else:
            arg_name = args.split("=", maxsplit=1)[0].strip()
        if arg_name not in self.vars:
            if not defaulting:
                return CommandFailure(f"Missing argument: {arg_name}")
            return await self.cmd_var(message, args)

    async def cmd_args(self, message: UserMessage, args: str) -> None | CommandFailure:
        """Returns a failure if any of the arguments have not been defined.
        Does nothing otherwise.
        This is typically used at the start of a script file, to ensure that every script input is defined.
        Names of arguments cannot contain commas, since commas are the separator. To define an argument with a comma,
        use the `arg` command instead.
        If an argument starts with ":", the value provided for the argument will be interpreted as a string literal.
        Usage:
        `args {name of argument}, {name of another argument}, :{and a string argument}, {and so on any number of times...}`
        """
        if self.vars._has_defaulting_args:
            return CommandFailure(
                "Arguments without defaults must precede arguments with defaults."
            )
        args_split = [arg.strip() for arg in args.split(",")]
        for arg in args_split:
            if arg.startswith(":"):
                arg = arg[1:]
            if arg not in self.vars:
                return CommandFailure(f"Missing argument: {args}")

    @slow_command
    async def cmd_load_text(self, message: UserMessage, args: str) -> str:
        """Load the text of a file and return it.
        Usage:
        `load_text {filename}`"""
        if "$FIC" in args:
            args = args.replace("$FIC", "./fictionsuit/fic")
        if "$.FIC" in args:
            args = args.replace("$.FIC", "./fictionsuit/.fic")
        try:
            with open(args, "r") as f:
                return f.read()
        except FileNotFoundError:
            return CommandFailure(f"File not found: {args}")

    @slow_command
    async def cmd_load_fic(self, message: UserMessage, args: str) -> str:
        """Load a fictionscript from a file. Files typically use the .fic extension. When this is the case, the
        name of the variable referring to the script will be the filename before the .fic extension, with
        underscores replaced by spaces, in all lower case.
        Usage:
        `load_fic fic/compose_poem.fic` by default, this will load the script as "compose poem"
        `load_fic fic/query.fic as {custom name}`"""
        if "$FIC" in args:
            used_shorthand = True
            args = args.replace("$FIC", "./fictionsuit/fic")
        if "$.FIC" in args:
            used_shorthand = True
            args = args.replace("$.FIC", "./fictionsuit/.fic")

        split = [x.strip() for x in args.split(" as ", maxsplit=1)]
        if len(split) == 1:
            var_name = ntpath.basename(args)
            if var_name.endswith(".fic"):
                var_name = var_name[:-4].replace("_", " ").lower()
        else:
            var_name = split[1]

        try:
            script = FictionScript.from_file(split[0], var_name)
        except FileNotFoundError:
            if used_shorthand:
                return CommandFailure(
                    f"File `{split[0]}` not found. Maybe you mixed up `$FIC` and `$.FIC`?"
                )
            return CommandFailure(f"File `{split[0]}` not found.")

        self.vars[var_name] = script

        return var_name

    async def cmd_echo(self, message: UserMessage, args: str) -> str:
        """Returns the arguments.
        Usage:
        `echo {text}`"""
        return args

    async def cmd_yell(self, message: UserMessage, args: str) -> str:
        """Returns the arguments, and replies to the message.
        This is distinct from echo in that it will reply even when called from within a script, which would normally disable replies.
        This should pretty much only be used for debugging, and should not appear in finished scripts.
        """
        previous_state = message.disable_interactions
        message.disable_interactions = False
        await message.reply(args)
        message.disable_interactions = previous_state
        return args

    async def cmd_dynamic_fic(
        self, message: UserMessage, args: str
    ) -> FictionScript | CommandFailure:
        """Executes its arguments, and attempts to parse the result as a fictionscript.
        Usage:
        `dynamic_fic {expression that returns a string that can be parsed as a fictionscript}`
        """
        result = await self._evaluate(message, args, "dynamic script provider")
        if isinstance(result, CommandFailure):
            return CommandFailure(
                f"Failed to evaluate dynamic fictionscript content provider:\n{result}"
            )
        if not isinstance(result, str):
            return CommandFailure(
                f"Dynamic fictionscript content provider returned a non-string:\n{result}"
            )
        try:
            return FictionScript(lines=result.split("\n"))
        except Exception as e:
            return CommandFailure(f"Failed to parse ficscript: {e}")

    @no_preprocessing_after("\n")
    @slow_command
    async def cmd_def_fic(self, message: UserMessage, args: str) -> str:
        """Define a fictionscript. You should probably look at some examples and README.md in the `fic/` folder, and
        familiarize yourself with the documentation of the commands from the `Scripting` command group.
        Usage:
        `def_fic {name}\\n{script}`"""
        split = [x.strip() for x in args.split("\n")]
        var_name = split[0]
        if len(split) < 2:
            return CommandFailure("Script definition is empty.")
        return FictionScript(split[1:], name=var_name)

    async def _fic(
        self,
        message: UserMessage,
        args: str,
        script: FictionScript,
        scope: Scope | None = None,
    ) -> CommandFailure:
        """Execute a fictionscript. If a scope is provided, the script will be executed in that scope.
        Otherwise, the script will execute inside a new temporary scope called "{script name} execution".
        """
        split = args.split(":", maxsplit=1)
        if len(split) > 1:
            arg_values = [
                x.strip().replace(COMMA_ESCAPE, ",") for x in split[1].split(",")
            ]
            arg_values = [x for x in arg_values if x != ""]
        else:
            arg_values = []
        params = script.args
        script_name = script.name

        previous_dis_int_value = message.disable_interactions
        message.disable_interactions = True

        initial_scope = self.vars
        if scope is not None:
            self.vars = scope
        else:
            self.vars = Scope(name=f"{script.name} execution", parent=self.vars)

        async def enqueue(script_message):
            return await self.system.enqueue_message(
                script_message, return_failures=True, return_returns=True
            )

        if len(arg_values) > len(params):
            message.disable_interactions = previous_dis_int_value
            self._return_to_scope(initial_scope)
            return CommandFailure(
                f"Too many arguments! Remember to escape your commas.\n\nExtra arguments:\n{arg_values[len(params):]}"
            )

        for i in range(len(arg_values)):
            echo = False
            arg_value = arg_values[i]
            param = params[i]
            if param.startswith(":"):
                param = param[1:]
                echo = True
            if arg_value.startswith(":"):
                arg_value = arg_value[1:]
                echo = True
            assignment_op = ":=" if echo else "="
            result = await enqueue(
                ScriptLineMessage(
                    f"var {param} {assignment_op} {arg_value}", script_name, message
                )
            )
            if result is not None:
                message.disable_interactions = previous_dis_int_value
                self._return_to_scope(initial_scope)
                return CommandFailure(f"Failed to set argument:\n{result}")

        message_lines = []
        collecting = False
        for index, line in enumerate(script.lines):
            line = line.rstrip()
            if line.endswith("--"):
                if not collecting:
                    if line[-3] == "-":
                        message_lines.append(line[:-3].rstrip())
                        collecting = True
                        continue
                    message_lines.append(line[:-2].rstrip())
                    continue
                line = line[:-2].rstrip()
                collecting = False
            else:
                if collecting:
                    message_lines.append(line)
                    continue
            message_lines.append(line)
            message_content = "\n".join(message_lines)
            if message_content.startswith("#"):
                message_lines = []
                continue
            if message_content == "":
                message_lines = []
                continue
            message = ScriptLineMessage("\n".join(message_lines), script_name, message)
            result = await enqueue(message)
            message_lines = []
            if isinstance(result, CommandFailure):
                message.disable_interactions = previous_dis_int_value
                self._return_to_scope(initial_scope)
                return CommandFailure(
                    f"Script `{script_name}` failed at line {index + 1}:\n{result}"
                )
            if result is not None:
                message.disable_interactions = previous_dis_int_value
                self._return_to_scope(initial_scope)
                return result

        self._return_to_scope(initial_scope)

        message.disable_interactions = previous_dis_int_value

    @escape_commas
    @slow_command
    async def cmd_fic(self, message: UserMessage, args: str) -> CommandFailure:
        """Run a fictionscript.
        This command will first check the current scope for the script, then the
        `fic` scope, which is automatically populated with the scripts in the `fic/` and `.fic/` folders.
        Finally, it will check the filesystem for the script.
        If the script returns a value, this command will return that value.
        Usage:
        `fic {name of script}: {arguments}`
        `<name of script> {arguments}` (shorthand)"""
        scope_before = self.vars
        disabled_before = message.disable_interactions
        try:
            split = args.split(":", maxsplit=1)
            script_name = split[0].strip()
            if len(split) > 1:
                arg_values = [
                    x.strip().replace(COMMA_ESCAPE, ",") for x in split[1].split(",")
                ]
                arg_values = [x for x in arg_values if x != ""]
            else:
                arg_values = []

            if script_name in self.vars:
                script = self.vars[script_name]
            elif script_name in self.vars["fic"]:
                script = self.vars["fic"][script_name]
            elif os.path.exists(script_name):
                script_name = await self.cmd_load_fic(message, script_name)
                script = self.vars[script_name]
            else:
                if ":" not in args:
                    return CommandFailure(
                        "No such script.\nMaybe you forgot to put a colon (:) after the script name?"
                    )
                return CommandFailure("No such script.")

            if not isinstance(script, FictionScript):
                return CommandFailure(f"{script_name} is not a script.")
            return await self._fic(message, args, script)
        finally:
            self._return_to_scope(scope_before)
            message.disable_interactions = disabled_before

    async def cmd_pack(self, message: UserMessage, args: str):
        """Copy several variables from the current scope into a new scope, and return it.
        If any of the variables are scopes, the new scope will become their parent.
        Usage:
        `pack {variable name}, {another variable}, {and so on...}`"""
        vars = [x.strip() for x in args.split(",")]
        scope = Scope(parent=self.vars, name="pack")

        for var in vars:
            if var in self.vars:
                scope[var] = self.vars[var]
                if isinstance(scope[var], Scope):
                    scope[var].parent = scope
            else:
                return CommandFailure(f'No variable "{var}" in scope.')
        return scope

    @no_preprocessing_after("")
    async def cmd_return(self, message: UserMessage, args: str):
        """Evaluate an expression and return its value.
        Outside of a script, `return {expr}` and `{expr}` are basically equivalent.
        If used inside a script, however, this will immediately end execution of the script,
        and cause the script to return the value.
        Usage:
        `return {expression}`"""
        return await self._evaluate(message, args, "return")

    async def _evaluate(
        self,
        message: UserMessage,
        expression: str,
        context: str,
        scope: Scope | None = None,
    ):
        """Evaluate an expression. If a scope is provided, the expression will be evaluated from within that scope."""
        previous_dis_int_value = message.disable_interactions
        message.disable_interactions = True
        initial_scope = self.vars
        if scope is not None:
            self.vars = scope
        expression_message = ExpressionMessage(expression, context, message)
        result = await self.system.enqueue_message(
            expression_message, return_whatever=True
        )
        message.disable_interactions = previous_dis_int_value
        self._return_to_scope(initial_scope)
        return result

    @no_preprocessing_after("=", unless=":=")
    @slow_command
    async def cmd_var(self, message: UserMessage, args: str):
        """Evaluates an expression and stores its result in a variable in the current scope.
        Fails if the expression returns no value.
        If ":=" is used instead of "=", the arguments will be interpreted as a string literal instead of being evaluated as an expression.
        Usage:
        `var {name of variable} = {expression}`
        `. {variable} = {expression}` (shorthand)
        `. {variable} := {string literal}`"""

        echo = ":=" in args
        if echo:
            arg_split = [x.strip() for x in args.split(":=", maxsplit=1)]
        else:
            arg_split = [x.strip() for x in args.split("=", maxsplit=1)]

        arg_split = [x for x in arg_split if x != ""]

        if len(arg_split) != 2:
            return CommandFailure("Failed to store variable: Invalid syntax.")

        scope = self.vars

        var_name = arg_split[0]
        while len(var_name) > 0 and var_name[0] == "." and scope.parent is not None:
            var_name = var_name[1:].lstrip()
            scope = scope.parent

        if echo:
            scope[var_name] = arg_split[1]
            return

        result = await self._evaluate(message, arg_split[1], "var")

        if isinstance(result, CommandFailure):
            return CommandFailure(f'Expression after "=" failed:\n{result}')

        if result is None:
            return CommandFailure(f'Expression after "=" returned no value.')

        scope[var_name] = result

        if isinstance(result, Scope):
            result.recontextualize(var_name, scope)

        if isinstance(result, ChatInstance):
            result.name = var_name

        if isinstance(result, FictionScript):
            result.name = var_name
