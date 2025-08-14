import __main__
import time
import ipaddress
from flask import make_response, request, jsonify
from core.error import restricted_access_error
from core.logging import logs


class Fail2Ban:
    def __init__(self, app, blacklist, whitelist, max_fail, fail_interval, ban_time):
        self.app = app
        self.blacklist = blacklist
        self.whitelist = whitelist
        self.max_fail = max_fail
        self.fail_interval = fail_interval
        self.ban_time = ban_time

        self.init_fail2ban()

    def init_fail2ban(self):
        self.failed_attempts = {}       # { ip: [timestamps] }
        self.ban_timestamps = {}        # { ip: ban_start_time }
        self.failed_attempts_threshold = self.max_fail
        self.failed_attempts_time_window = self.fail_interval

        @self.app.before_request
        def block_banned_ips():
            ip = self.get_client_ip()
            if ip in self.ban_timestamps:
                ban_start = self.ban_timestamps[ip]
                if time.time() - ban_start < self.ban_time:
                    logs(f"IP {ip} temporairement bloquée pour activité suspecte", status='info', component='system')
                    if request.path.startswith('/api'):
                         return jsonify({"error": "Votre accès est temporairement bloquée"}), 403
                    else:
                        return make_response("Votre accès est temporairement bloquée.", 403)
                else:
                    # Déban automatique après expiration
                    del self.ban_timestamps[ip]
                    self.failed_attempts.pop(ip, None)  # Réinitialiser les échecs aussi

        #logs(f"Auto-protection activée", status='success', component='system')


    def handle_failed_attempt(self, ip):
        now = time.time()
        attempts = self.failed_attempts.get(ip, [])
        attempts = [ts for ts in attempts if now - ts < self.failed_attempts_time_window]
        attempts.append(now)
        self.failed_attempts[ip] = attempts

        if len(attempts) >= self.failed_attempts_threshold:
            self.ban_timestamps[ip] = now
            print(f"IP {ip} a été temporairement bannie pour {self.ban_time} secondes.")

    def auto_protect(self):
        ip = self.get_client_ip()
        if self.is_ip_blacklisted(ip):
            if request.path.startswith('/api'):
                return jsonify({"error": "Votre accès est restreint pendant une durée indéterminée"}), 403
            else:
                return make_response(restricted_access_error(), 403)

        if not self.is_ip_whitelisted(ip):
            self.handle_failed_attempt(ip)

    def get_client_ip(self):
        return request.remote_addr

    def is_ip_whitelisted(self, ip):
        try:
            client_ip = ipaddress.ip_address(ip)
            return any(client_ip in ipaddress.ip_network(entry, strict=False) for entry in self.whitelist)
        except ValueError:
            return False

    def is_ip_blacklisted(self, ip):
        try:
            client_ip = ipaddress.ip_address(ip)
            return any(client_ip in ipaddress.ip_network(entry, strict=False) for entry in self.blacklist)
        except ValueError:
            return False