from users.useCases.logOut.OutputData import LogOutOutputData


class LogOutPresenter:
    response_body: dict = {}
    status_code = 200

    def present(self, output: LogOutOutputData) -> None:
        self.response_body = {"detail": "Logged out."}
        self.status_code = output.status_code
