from flask import request, has_request_context, has_app_context
from models.database import db, LogSystem, LogWeb, LogApi
from views.utils import construct_context
from zpp_color import fg, attr
from datetime import datetime
import logging
import sys
import __main__
import re

def remove_ansi_codes(s: str) -> str:
    """Removes ANSI escape codes from a string."""
    ansi_escape = re.compile(r'\x1b\[([0-9;]*m)')
    return ansi_escape.sub('', s)


def logs(message, status, component, user_id=None, request_info=None, result=None, api_name=None, token=None):
    if status=='logs':
        color = "light_gray"
    elif status=='info':
        color = "cyan"
    elif status=='warning' or status=='unauthorized':
        color = "yellow"
    elif status=='error' or status=='bad_request':
        color = "red"
    elif status=='critical':
        color = "light_red"
    elif status=='success':
        color = "green"
    elif status=='debug':
        color = "magenta"

    """
    Adds a new log entry to the appropriate log table.
    """
    if has_request_context():
        context = construct_context()

        if not user_id:
            user_id = context.get('user_id', None)


        ip_address = request.remote_addr
    else:
        ip_address = None
        user_id = None

    date = datetime.now().strftime("%Y/%m/%d - %H:%M:%S.%f")
    print_date = f"{fg('dark_gray')}[{attr(0)}{fg('magenta')}{date}{attr(0)}{fg('dark_gray')}] - {attr(0)}"

    print_component = f"{fg('dark_gray')}[{attr(0)}{fg('yellow')}{component.upper()}{attr(0)}{fg('dark_gray')}] - {attr(0)}"
    print_component = f"{fg('dark_gray')}[{attr(0)}{fg(color)}{component.upper()}{attr(0)}{fg('dark_gray')}] - {attr(0)}"

    print(f"{print_date}{print_component}{fg('cyan')}{message}{attr(0)}")

    if has_app_context():
        if component == 'system':
            log_entry = LogSystem(
                level=status,
                message=message,
                details=result if result else '',
            )
        elif component == 'web':
            log_entry = LogWeb(
                user_id=user_id,
                ip_address=ip_address,
                request=request_info,
                status=status,
                message=message
            )
        elif component == 'api':
            log_entry = LogApi(
                token=token, # In API logs, user_id is the token_id
                ip_address=ip_address,
                request=request_info,
                status=status,
                response=result if result else '',
                message=message,
                name=api_name
            )
        else:
            return # Or raise an error for invalid component

        db.session.add(log_entry)
        db.session.commit()


def flash_notification(message, status):
    __main__.backend.notification_queue.append((message, status))


class CustomWerkzeugLogHandler(logging.Handler):
    def emit(self, record):
        # Check if this is an access log record based on its message and arguments structure
        # Access logs typically have record.msg as a format string with %s for request, status, size
        # and record.args will contain the actual values for those %s.
        # Also, the record.msg usually starts with an IP address.
        if isinstance(record.msg, str) and record.args and len(record.args) >= 2 and \
           record.msg.count('%s') >= 2 and record.msg.split(' ')[0].count('.') >= 3: # Simple check for IP
            try:
                ip_address = record.msg.split(' ')[0]
                request_line = record.args[0]
                status_code = str(record.args[1]) # Ensure status_code is a string for .startswith()

                request_parts = request_line.split(' ')
                method = request_parts[0]
                path = request_parts[1]

                method = remove_ansi_codes(method)

                dt_object = datetime.fromtimestamp(record.created)
                formatted_time = dt_object.strftime("%Y/%m/%d - %H:%M:%S.%f")

                if status_code.startswith('2'):
                    status_color = "green"
                elif status_code.startswith('3'):
                    status_color = "magenta"
                elif status_code.startswith('4'):
                    status_color = "yellow"
                elif status_code.startswith('5'):
                    status_color = "red"
                else:
                    status_color = "light_gray"

                log_message = (
                    f"{fg('dark_gray')}[{attr(0)}{fg('magenta')}{formatted_time}{fg('dark_gray')}] - "
                    f"{fg('dark_gray')}[{attr(0)}{fg('magenta')}SOCKET{fg('dark_gray')}] - "
                    f"{attr(0)}{fg('light_gray')}{ip_address}{fg('dark_gray')} - "
                    f"[{fg('cyan')}{method}{fg('dark_gray')}] - "
                    f"[{attr(0)}{fg(status_color)}{status_code}{fg('dark_gray')}] - "
                    f"{attr(0)}{fg('cyan')}{path}{attr(0)}"
                )
                print(log_message, file=sys.stdout)

            except Exception as e:
                # If parsing fails for an assumed access log, print the original message
                # and the error for debugging.
                print(f"Error parsing Werkzeug access log: {e}", file=sys.stderr)
                print(self.format(record), file=sys.stdout) # Fallback to default formatting

        else:
            # For other types of log records (e.g., startup messages),
            # just print the default formatted message.
            print(self.format(record), file=sys.stdout)