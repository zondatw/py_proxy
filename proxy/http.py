
def http_request_parse(request):
    http_request = HTTPRequest()
    http_request.parse(request)
    return http_request

def http_response_parse(response):
    http_response = HTTPResponse()
    http_response.parse(response)
    return http_response


class Header:
    pass


class HTTPRequest:
    def __init__(self):
        self.method = ""
        self.request_target = ""
        self.http_version = ""
        self.header = Header()
        self.body = b""

    def parse(self, request):
        request_block = request.split(b"\r\n")
        request_block.reverse()

        # start line
        start_line = request_block.pop().decode(errors="ignore")
        self.method, self.request_target, self.http_version = start_line.split(" ")

        # header
        header_field = request_block.pop().decode(errors="ignore")
        while header_field != "":
            field_name, field_value = header_field.split(": ")
            self.header.__setattr__(field_name, field_value)
            header_field = request_block.pop().decode(errors="ignore")

        # body
        self.body = request_block.pop()

    def __str__(self):
        http_request = []
        http_request.append(f"{self.method} {self.request_target} {self.http_version}")
        for field_name, field_value in self.header.__dict__.items():
            http_request.append(f"{field_name}: {field_value}")
        http_request.append("")
        http_request.append(str(self.body))
        return "\r\n".join(http_request)


class HTTPResponse:
    def __init__(self):
        self.http_version = ""
        self.status_code = ""
        self.status_msg = ""
        self.header = Header()
        self.body = b""

    def parse(self, response):
        response_block = response.split(b"\r\n")
        response_block.reverse()

        # start line
        start_line = response_block.pop().decode(errors="ignore")
        start_line_block = start_line.split(" ")
        self.http_version = start_line_block[0]
        self.status_code = start_line_block[1]
        self.status_msg = " ".join(start_line_block[2:])

        # header
        header_field = response_block.pop().decode(errors="ignore")
        while header_field != "":
            field_name, field_value = header_field.split(": ")
            self.header.__setattr__(field_name, field_value)
            header_field = response_block.pop().decode(errors="ignore")

        # body
        self.body = response_block.pop()

    def __str__(self):
        http_response = []
        http_response.append(f"{self.http_version} {self.status_code} {self.status_msg}")
        for field_name, field_value in self.header.__dict__.items():
            http_response.append(f"{field_name}: {field_value}")
        http_response.append("")
        http_response.append(str(self.body))
        return "\r\n".join(http_response)