import libtmux


class TmuxManager:
    def __init__(self, *, session_name: str) -> None:
        self.session_name = session_name
        self.tmux_server = libtmux.Server()

    def start_tmux_session(self) -> None:
        self.tmux_server.cmd("new-session", "-d", "-s", self.session_name)

    @property
    def tmux_session(self) -> libtmux.Session | None:
        return self.tmux_server.sessions.get(name=self.session_name)

    @property
    def tmux_window(self) -> libtmux.Window | None:
        return self.tmux_session.windows[0]

    @property
    def tmux_pane(self) -> libtmux.Pane | None:
        return self.tmux_window.panes[0]

    def send_command(self, command: str) -> None:
        self.start_tmux_session()
        self.tmux_pane.send_keys(command)
