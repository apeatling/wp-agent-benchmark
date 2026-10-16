"""Building with the site owner, for harnesses beyond Claude Code and Codex: Antigravity and Grok Build.

Each uses the same harness wrapper as in Choosing (wpab.agents), so sign-in, the sandbox and session continuation
are the same, but without the one-off nudge: in Building the owner's replies take its place (see SiteOwner). The
connector for the official and third-party setups comes from the task (task.toml, environment.mcp_servers), which
Harbor writes into each harness's own settings: ~/.gemini/antigravity-cli/settings.json (mcpServers.<name>.httpUrl)
for Antigravity, ~/.grok/config.toml ([mcp_servers.<name>] url) for Grok Build.

Kept apart from wpab.agents so a batch that's already running, which re-imports that module for every run, isn't
touched.
"""
import json
import re
from pathlib import Path

from harbor.agents.installed.antigravity_cli import AntigravityCli as HarborAntigravityCli
from harbor.agents.installed.grok_build import GrokBuild as HarborGrokBuild

from .agents import AntigravityCli, GrokBuild, SiteOwner


def _questions(value):
    """The question texts in a tool's input (Antigravity's ask_question, Grok's ask_user_question)."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return [value]
    if isinstance(value, dict):
        own = [value['question']] if isinstance(value.get('question'), str) else []
        return own + [q for k, v in value.items() if k != 'question' for q in _questions(v) if isinstance(v, (dict, list))]
    if isinstance(value, list):
        return [q for v in value for q in _questions(v)]
    return []


def _is_connector(name, raw=None):
    """Whether a tool call went to the connector. The harnesses name connector tools after the server
    ("wordpress" in every task) or with an mcp prefix; Grok can also reach them through use_tool."""
    name = (name or '').lower()
    if name == 'use_tool':
        return bool(re.search(r'mcp|wordpress', json.dumps(raw or {}).lower()))
    return name.startswith(('mcp', 'wordpress')) or '__' in name


class OwnerTurns(SiteOwner):
    """SiteOwner, with the run's workarounds and connector calls read from these harnesses' own output."""

    @staticmethod
    def commands(text):
        raise NotImplementedError

    async def run(self, instruction, environment, context):
        first = not self._resume and not self._load
        await super().run(instruction, environment, context)
        if not first:
            return
        from . import owner
        logs = Path(self.logs_dir)
        found, mcp = {}, 0
        for f in sorted(logs.glob(f'turn-*-{self.STREAM}')):
            cmds, n = self.commands(f.read_text(errors='replace'))
            mcp += n
            for name, pattern in owner.WORKAROUNDS.items():
                hits = sum(1 for c in cmds if all(re.search(p, c) for p in pattern))
                if hits:
                    found[name] = found.get(name, 0) + hits
        path = logs.parent / 'wpab.json'
        data = json.loads(path.read_text()) if path.exists() else {}
        if 'owner' in data:
            data['owner'].update(workarounds=found, connector_calls=mcp)
            path.write_text(json.dumps(data, indent=2))


class _AntigravityTurns(AntigravityCli):
    """Antigravity as in Choosing (the conversation continued by its ID), without the nudge, and with each turn's
    part of the transcript written to its own file.

    agy's stream output has only progress events, no text, so a turn's messages come from the transcript Harbor
    copies out after every turn (antigravity-cli.trajectory.jsonl). That holds the whole conversation; the turn is
    everything from its last user input on.
    """
    TURN_FILE = 'antigravity-turn.txt'
    TRANSCRIPT = 'antigravity-cli.trajectory.jsonl'
    # In Choosing a turn is short and ten minutes stops one waiting on a dev server it started. A Building turn can
    # be real work on a site, so it gets longer; the task's own time limit still covers the whole run.
    _PRINT_TIMEOUT = '30m'

    async def run(self, instruction, environment, context):
        first = not self._resume and not self._load
        logs = Path(self.logs_dir)
        # So a turn that fails to write a transcript isn't read as the one before it.
        (logs / self.TRANSCRIPT).unlink(missing_ok=True)
        (logs / self.TURN_FILE).unlink(missing_ok=True)
        try:
            await HarborAntigravityCli.run(self, instruction, environment, context)
        finally:
            if first:  # kept even when the turn times out, so the owner's reply reaches the same conversation
                self._conversation_id = self._read_conversation_id()
                self._id_file().write_text(json.dumps({'conversation_id': self._conversation_id}))
            self._write_turn()

    def _write_turn(self):
        logs = Path(self.logs_dir)
        path = logs / self.TRANSCRIPT
        records = (HarborAntigravityCli._load_step_transcript(path) or []) if path.exists() else []
        start = max((i for i, r in enumerate(records) if str(r.get('type')).upper() == 'USER_INPUT'), default=0)
        (logs / self.TURN_FILE).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records[start:]))


class AntigravityCliWithOwner(OwnerTurns, _AntigravityTurns):
    STREAM = _AntigravityTurns.TURN_FILE

    @staticmethod
    def _records(text):
        for line in text.splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict):
                yield r

    def _last_message(self, text):
        """The agent's last message in the turn, and any questions it put to the owner with its ask_question tool
        after that (in a headless run nobody answers them there, so the owner answers in the next turn)."""
        out, asked = None, []
        for r in self._records(text):
            if str(r.get('type')).upper() != 'PLANNER_RESPONSE':
                continue
            if isinstance(r.get('content'), str) and r['content'].strip():
                out, asked = r['content'].strip(), []
            for call in r.get('tool_calls') or []:
                if isinstance(call, dict) and call.get('name') == 'ask_question':
                    asked += _questions((call.get('args') or {}).get('questions'))
        if asked:
            out = (out + '\n\n' if out else '') + '\n'.join(asked)
        return out

    @staticmethod
    def commands(text):
        out, mcp = [], 0
        for r in AntigravityCliWithOwner._records(text):
            for call in r.get('tool_calls') or [] if str(r.get('type')).upper() == 'PLANNER_RESPONSE' else []:
                if not isinstance(call, dict):
                    continue
                args = call.get('args') if isinstance(call.get('args'), dict) else {'value': call.get('args')}
                if _is_connector(call.get('name')):
                    mcp += 1
                out.append(args.get('CommandLine') or json.dumps(args))
        return out, mcp


class _GrokTurns(GrokBuild):
    """Grok Build as in Choosing (the session continued with --resume), without the nudge.

    Harbor's exit watchdog treats a turn as over once the session's events file has a turn_ended event. A resumed
    session's file already has one from the turn before, so on later turns the watchdog would start stopping the
    agent's commands two minutes in. Here it waits for a turn_ended beyond the ones already there.
    """
    _TURN_ENDED = """grep -qs '"type":"turn_ended"' {events} || continue"""

    async def run(self, instruction, environment, context):
        if not self._resume and not self._load:
            # Saved before the turn, so the owner's reply can continue it even if this turn times out.
            self._id_file().write_text(json.dumps({'session_id': self._session_id}))
        (Path(self.logs_dir) / self._OUTPUT_FILENAME).unlink(missing_ok=True)  # a turn that writes nothing isn't read as the last
        await HarborGrokBuild.run(self, instruction, environment, context)

    def _build_run_script(self, escaped_instruction):
        script = super()._build_run_script(escaped_instruction)
        events = f'"$HOME"/.grok/sessions/*/{self._session_id}/events.jsonl'
        count = f"""$(cat {events} 2>/dev/null | grep -c '"type":"turn_ended"')"""
        old = self._TURN_ENDED.format(events=events)
        if old not in script:
            if self.options.kill_leftover_processes:
                raise RuntimeError("Harbor's Grok Build run script has changed; check the turn_ended watchdog patch.")
            return script
        script = script.replace(old, f'[ "{count}" -gt "$WPAB_TURNS_BEFORE" ] || continue')
        return script.replace(self._PATH_EXPORT, f'{self._PATH_EXPORT}\nWPAB_TURNS_BEFORE={count}', 1)


class GrokBuildWithOwner(OwnerTurns, _GrokTurns):
    STREAM = HarborGrokBuild._OUTPUT_FILENAME

    @staticmethod
    def _events(text):
        for line in text.splitlines():
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if isinstance(m, dict):
                yield m

    def _last_message(self, text):
        """The text Grok streamed after its last tool call (its closing message), and any questions it put to the
        owner with ask_user_question after its last message."""
        parts, asked, after_tool = [], [], False
        for m in self._events(text):
            t = m.get('type')
            if t == 'tool_call':
                after_tool = True
                if m.get('toolName') == 'ask_user_question':
                    asked += _questions(m.get('rawInput'))
            elif t == 'text' and isinstance(m.get('data'), str):
                if after_tool:
                    parts, asked, after_tool = [], [], False
                parts.append(m['data'])
        out = ''.join(parts).strip() or None
        if asked:
            out = (out + '\n\n' if out else '') + '\n'.join(asked)
        return out

    @staticmethod
    def commands(text):
        out, mcp, seen = [], 0, set()
        for m in GrokBuildWithOwner._events(text):
            if m.get('type') != 'tool_call' or m.get('toolCallId') in seen:
                continue
            seen.add(m.get('toolCallId'))
            raw = m.get('rawInput') if isinstance(m.get('rawInput'), dict) else {}
            if _is_connector(m.get('toolName'), raw):
                mcp += 1
            out.append(raw.get('command') or json.dumps(raw))
        return out, mcp
