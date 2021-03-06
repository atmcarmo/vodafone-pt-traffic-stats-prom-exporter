"""Vodafone PT HG8247X6-8N Prometheus Exporter with WAN/LAN/WLAN traffic statistics"""

import os
import time
import requests
import re
from prometheus_client import start_http_server, Counter
from distutils.util import strtobool

class VodafoneMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    Vodafone router statistics into Prometheus metrics.
    """

    bytes_counter_suffix = "bytes_total" # suffix for counter metrics
    bytes_counter_prefix = "vodafone" # suffix for counter metrics

    def __init__(self, polling_interval_seconds=60):
        self.polling_interval_seconds = polling_interval_seconds

        self.host = os.environ.get('ROUTER_HOST')
        self.username = os.environ.get('ROUTER_USERNAME')
        self.password = os.environ.get('ROUTER_PASSWORD')
        try:
            self.use_wan_multipler = not bool(strtobool(os.environ.get("DISABLE_WAN_MULTIPLER")))
        except:
            self.use_wan_multipler = True

        # this is a multipler to try to fix the problem that happens when the LAN bytes achieve MAX INT and then reset to 0. 
        # while for LAN or WLAN the router itself has this counter, for WAN it doesn't have so we are basically manipulating here the raw values the router gives us
        self.wan_up_multiplier = 1
        self.wan_down_multiplier = 1
        # the previous values for WAN so that we can increment the multipler while comparing to the current raw value
        self.wan_up_previous_value = 0
        self.wan_down_previous_value = 0

        # Prometheus metrics to collect
        self.wan_bytes_up = Counter(self.build_counter_metric("wan", "up"), "Total bytes upload")
        self.wan_bytes_down = Counter(self.build_counter_metric("wan", "down"), "Total bytes download")
        self.lan1_bytes_down = Counter(self.build_counter_metric("lan1", "down"), "LAN1 Total bytes download")
        self.lan1_bytes_up = Counter(self.build_counter_metric("lan1", "up"), "LAN1 Total bytes upload")
        self.lan2_bytes_down = Counter(self.build_counter_metric("lan2", "down"), "LAN2 Total bytes download")
        self.lan2_bytes_up = Counter(self.build_counter_metric("lan2", "up"), "LAN2 Total bytes upload")
        self.lan3_bytes_down = Counter(self.build_counter_metric("lan3", "down"), "LAN3 Total bytes download")
        self.lan3_bytes_up = Counter(self.build_counter_metric("lan3", "up"), "LAN3 Total bytes upload")
        self.lan4_bytes_down = Counter(self.build_counter_metric("lan4", "down"), "LAN4 Total bytes download")
        self.lan4_bytes_up = Counter(self.build_counter_metric("lan4", "up"), "LAN4 Total bytes upload")
        self.wifi_2_4_bytes_down = Counter(self.build_counter_metric("wifi_2_4ghz", "down"), "WIFI 2.4GHz Total bytes download")
        self.wifi_2_4_bytes_up = Counter(self.build_counter_metric("wifi_2_4ghz", "up"), "WIFI 2.4 GHz Total bytes upload")
        self.wifi_5_bytes_down = Counter(self.build_counter_metric("wifi_5ghz", "down"), "WIFI 5 GHz Total bytes download")
        self.wifi_5_bytes_up = Counter(self.build_counter_metric("wifi_5ghz", "up"), "WIFI 5 GHz Total bytes upload")


    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            try:
                self.fetch()
            finally:
                time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        LOGIN_COOKIE = dict(Cookie="body:Language:portuguese:id=1")

        """Get the raw string with the devices from the router."""
        cnt = requests.post(f"http://{self.host}/asp/GetRandCount.asp")
        cnt_str = str(cnt.content, cnt.apparent_encoding, errors="replace")

        cookie = requests.post(
            f"http://{self.host}/login.cgi",
            data=[
                ("UserName", self.username),
                ("PassWord", self.password),
                ("x.X_HW_Token", cnt_str),
            ],
            cookies=LOGIN_COOKIE,
        )

        self.fetch_wan(cookie)
        self.fetch_lan(cookie)

    def fetch_wan(self, cookie):
        """
        WAN metrics
        """
        page = requests.get(
            f"http://{self.host}/html/bbsp/wanStats/wanStatus_ptvdf.asp",
            cookies=cookie.cookies,
        )

        html=page.content.decode(page.apparent_encoding).encode().decode("unicode_escape")
 
        regex=r"InternetGatewayDevice\.WANDevice\.1\.WANConnectionDevice\.1\.WANIPConnection\.1\.Stats\"\,\"\d+\"\,\"(\d+)\"\,\"\d+\"\,\"\d+\"\,\"\d+\"\,\"(\d+)"
        matches = re.search(regex,html)
        up_raw = int(matches.groups()[0])
        down_raw = int(matches.groups()[1])

        # if we find that the current value is less than the previous value it means it reached max int in the router and we increment our own multipler
        # this may help but with a fast enough connection it may reach max int several times between each time the exporter runs
        # if that's the case the multipler will only increment by one time and we have no way of knowing that
        if (self.use_wan_multipler):
            if (up_raw < self.wan_up_previous_value):
                self.wan_up_multiplier += 1
                self.wan_up_previous_value = up_raw

            if (down_raw < self.wan_down_previous_value):
                self.wan_down_multiplier += 1
                self.wan_down_previous_value = down_raw

        # Update Prometheus metrics with application metrics
        self.wan_bytes_up._value.set(up_raw * self.wan_up_multiplier)
        self.wan_bytes_down._value.set(down_raw * self.wan_down_multiplier)

    def fetch_lan(self, cookie):
        """
        LAN metrics
        """
        page = requests.get(
            f"http://{self.host}/html/bbsp/landhcp/landhcp_ptvdf.asp",
            cookies=cookie.cookies,
        )

        html=page.content.decode(page.apparent_encoding).encode().decode("unicode_escape")
 
        # TODO: this needs to be improved. I literaly hardcoded the regex and copy and pasted the calculations for each LAN port.
        #lan1
        regexLan1=r"InternetGatewayDevice\.X_HW_DEBUG\.AMP\.LANPort\.1\.Statistics\D+(\d+)\D+(\d+)\"(?:\,\"\d+\"){4}\D+(\d+)\D+(\d+)"
        matchesLan1 = re.search(regexLan1,html)
        self.lan1_bytes_up._value.set(self.get_lan_bytes_up(matchesLan1))
        self.lan1_bytes_down._value.set(self.get_lan_bytes_down(matchesLan1))

        #lan2
        regexLan2=r"InternetGatewayDevice\.X_HW_DEBUG\.AMP\.LANPort\.2\.Statistics\D+(\d+)\D+(\d+)\"(?:\,\"\d+\"){4}\D+(\d+)\D+(\d+)"
        matchesLan2 = re.search(regexLan2,html)
        self.lan2_bytes_up._value.set(self.get_lan_bytes_up(matchesLan2))
        self.lan2_bytes_down._value.set(self.get_lan_bytes_down(matchesLan2))

        #lan3
        regexLan3=r"InternetGatewayDevice\.X_HW_DEBUG\.AMP\.LANPort\.3\.Statistics\D+(\d+)\D+(\d+)\"(?:\,\"\d+\"){4}\D+(\d+)\D+(\d+)"
        matchesLan3 = re.search(regexLan3,html)
        self.lan3_bytes_up._value.set(self.get_lan_bytes_up(matchesLan3))
        self.lan3_bytes_down._value.set(self.get_lan_bytes_down(matchesLan3))

        #lan3
        regexLan4=r"InternetGatewayDevice\.X_HW_DEBUG\.AMP\.LANPort\.4\.Statistics\D+(\d+)\D+(\d+)\"(?:\,\"\d+\"){4}\D+(\d+)\D+(\d+)"
        matchesLan4 = re.search(regexLan4,html)
        self.lan4_bytes_up._value.set(self.get_lan_bytes_up(matchesLan4))
        self.lan4_bytes_down._value.set(self.get_lan_bytes_down(matchesLan4))

        self.fetch_wlan(html)

    def fetch_wlan(self, html):
        """
        WLAN metrics
        """
        regex=r"(?<=new\sstPacketInfo\()\".*?\",\"(\d+)\",\"\d+\",\"(\d+)\",\"\d+\"(?=\))"
        matches = re.findall(regex,html)
        # Position 0 is for down statistics while position 1 is for up statistics
        wifi_2_4_down = int(matches[0][0])
        wifi_2_4_up = int(matches[0][1])
        wifi_5_down = int(matches[2][0])
        wifi_5_up = int(matches[2][1])

        # this is required because sometimes it seems that, for some reason, for wifi stats, the router returns 0 leading to Prometheus to interpret it as a counter reset
        if (wifi_2_4_down > 0):
            self.wifi_2_4_bytes_down._value.set(wifi_2_4_down)

        if (wifi_2_4_up > 0):
            self.wifi_2_4_bytes_up._value.set(wifi_2_4_up)

        if (wifi_5_down > 0):
            self.wifi_5_bytes_down._value.set(wifi_5_down)
        
        if (wifi_5_up > 0):
            self.wifi_5_bytes_up._value.set(wifi_5_up)

    def build_counter_metric(self, stats_name, up_or_down):
        """
        Auxiliar method to build a string to create the counter metric based on some parameters.
        """
        return f"{self.bytes_counter_prefix}_{stats_name}_{up_or_down}_{self.bytes_counter_suffix}"

    def get_lan_bytes_up(self, matchesLan):
        """
        Gets the LAN bytes for upstream
        """

        # aperently the way LAN statistics for each port are reset at this max int number
        # then, they are multiplied by the multiplier and finally they add the current bytes statistics
        max_int = 4294967296

        lan_up_multiplier = int(matchesLan.groups()[0])
        lan_up_bytes = int(matchesLan.groups()[1])
        lan_up_final_bytes = lan_up_multiplier * max_int + lan_up_bytes

        return lan_up_final_bytes
    
    def get_lan_bytes_down(self, matchesLan):
        """
        Gets the LAN bytes for downstream
        """

        # aperently the way LAN statistics for each port are reset at this max int number
        # then, they are multiplied by the multiplier and finally they add the current bytes statistics
        max_int = 4294967296

        lan_down_multiplier = int(matchesLan.groups()[2])
        lan_down_bytes = int(matchesLan.groups()[3])
        lan_down_final_bytes = lan_down_multiplier * max_int + lan_down_bytes
        
        return lan_down_final_bytes

def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "60")) # avoid having very low values. I don't recomend anything bellow 30 seconds.
    exporter_port = int(os.getenv("EXPORTER_PORT", "8081"))

    vodafone_metrics = VodafoneMetrics(
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    vodafone_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()