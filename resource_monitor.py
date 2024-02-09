import psutil
import time
import os

def yellow_str(input_string):
    return f"\u001b[33m{input_string}\u001b[0m"
    
def red_str(input_string):
    return f"\u001b[31m{input_string}\u001b[0m"
    
def green_str(input_string):
    return f"\u001b[32m{input_string}\u001b[0m"

class ComputerData:
    def __init__(self):
        self.bytes_data = None
        self.up_bytes_per_sec = 0
        self.down_bytes_per_sec = 0
        
    def get_bytes_per_sec(self):
        new_bytes_data = psutil.net_io_counters()
        try:
            self.up_bytes_per_sec = new_bytes_data.bytes_sent - self.bytes_data.bytes_sent
            self.down_bytes_per_sec = new_bytes_data.bytes_recv - self.bytes_data.bytes_recv
            self.bytes_data = new_bytes_data
        except:
            self.bytes_data = new_bytes_data
        
    def get_memory_usage(self):
        memory_info = psutil.virtual_memory()
        return memory_info.used, memory_info.total, memory_info.percent

    def get_cpu_usage(self):
        cpu_percent = psutil.cpu_percent(percpu=True)
        return cpu_percent
        
    def get_cpu_freq(self):
        freq = psutil.cpu_freq(percpu=False)
        return str(f"{round(freq.current,1)}GHz")
        
    def pretty_mem_bytes(self,byte_int: int) -> str:
        if byte_int >= 1073741824:
            byte_int = round(byte_int/1073741824,1)
            byte_str = f"{byte_int}GB"
        else:
            byte_int = round(byte_int/1048576)
            byte_str = f"{byte_int}MB"
        return byte_str
        
    def get_temp(self,fahrenheit=False, show_all=False):
        if fahrenheit:
            degrees = "F"
        else:
            degrees = "C"
        temps = psutil.sensors_temperatures(fahrenheit=fahrenheit)
        temp_lines = []
        longest_line = 0
        for major_device in temps:
            for minor_device in temps[major_device]:
                if show_all or minor_device.label != '' and minor_device.current != 0:
                    device_name = minor_device.label
                    if device_name == '':
                        device_name = "Unnamed"
                    temperature = str(minor_device.current) + degrees
                    try:
                        if minor_device.current >= minor_device.critical:
                            line = f"[{device_name:15}: {red_str(temperature):>5}]"
                        elif minor_device.current >= minor_device.high:
                            line = f"[{device_name:15}: {yellow_str(temperature):>5}]"
                        else:
                            line = f"[{device_name:15}: {temperature:>5}]"
                    except TypeError:
                        line = f"[{device_name:15}: {temperature:>5}]"
                    longest_line = max(longest_line,len(line))
                    temp_lines.append(line)
        header = "Temperatures"
        temp_lines.insert(0,f"{header:^{longest_line}}")
        return temp_lines
                        
    def bar_from_percent(self, percent):
        bar_amount = percent//5
        bar_str = int(bar_amount)*'|' + (20-int(bar_amount))*' '
        if percent > 95:
            bar_str = red_str(bar_str)
        elif percent > 65:
            bar_str = yellow_str(bar_str)
        else:
            bar_str = green_str(bar_str)
        return bar_str
                        
    def get_cpu_strings(self, cpu_padding):
        cpu_percent = self.get_cpu_usage()
        cpu_output_strings = []
        for cpu_int in range(0,len(cpu_percent)):
            cpu_num = f"{cpu_int}"
            cpu_bar_str = self.bar_from_percent(cpu_percent[cpu_int])
            cpu_output_strings.append(f"{cpu_num:>4}[{cpu_bar_str:<20} {int(cpu_percent[cpu_int]):{cpu_padding}}%]")
        return cpu_output_strings
            
    def get_ram_string(self, ram_padding):
        ram_used, ram_total, ram_percent = self.get_memory_usage()
        mem_bar_str = self.bar_from_percent(ram_percent)
        ram_used_str = self.pretty_mem_bytes(ram_used)
        ram_total_str = self.pretty_mem_bytes(ram_total)
        memory_percent_str = f"{ram_used_str}/{ram_total_str}"
        ram_output_string = f" Mem[{mem_bar_str:<20}{memory_percent_str:>{ram_padding}}]"
        return ram_output_string
        
    def get_disk_strings(self):
        output_strings = []
        partitions = psutil.disk_partitions()
        largest_partition_str = 0
        for partition in partitions:
            p_usage = psutil.disk_usage(partition.mountpoint)
            disk_name = partition.device[-4:]
            disk_used_str = self.pretty_mem_bytes(p_usage.used)
            disk_total_str = self.pretty_mem_bytes(p_usage.total)
            disk_bar_str = self.bar_from_percent(p_usage.percent)
            disk_percent_str = f"{disk_used_str}/{disk_total_str}"
            largest_partition_str = max(largest_partition_str,len(f"{disk_name}[{disk_bar_str:<20}{disk_percent_str}]"))
        # I am not sure how to properly get the largest and format this at the same time
        for partition in partitions:
            p_usage = psutil.disk_usage(partition.mountpoint)
            disk_name = partition.device[-4:]
            disk_used_str = self.pretty_mem_bytes(p_usage.used)
            disk_total_str = self.pretty_mem_bytes(p_usage.total)
            disk_bar_str = self.bar_from_percent(p_usage.percent)
            disk_percent_str = f"{disk_used_str}/{disk_total_str}"
            output_strings.append(f"{disk_name}[{disk_bar_str:<20}{disk_percent_str:>{largest_partition_str-35}}]")
        return output_strings
        
    def print_all_usage(self):
        disk_output = self.get_disk_strings()
        longest_line = 0
        for line in disk_output:
            longest_line = max(longest_line,len(line))
        temperature_output = self.get_temp()
        ram_padding = longest_line-35
        ram_output = self.get_ram_string(ram_padding)
        disk_len = longest_line-9
        cpu_padding = longest_line-37
        
        cpu_output = self.get_cpu_strings(cpu_padding)
        header = "Usage"
        left_output = cpu_output
        left_output.insert(0,f"{header:^{disk_len}}")
        left_output.append(ram_output)
        for line in disk_output:
            left_output.append(line)
        left_output.append(f"  Up[{self.up_bytes_per_sec:>{longest_line-28}} Bytes/Second]")
        left_output.append(f"Down[{self.down_bytes_per_sec:>{longest_line-28}} Bytes/Second]")
        while len(temperature_output) < len(left_output):
            temperature_output.append('')
        while len(temperature_output) > len(left_output):
            left_output.append(' '*disk_len)
        for line in range(0,len(cpu_output)):
            print(f"{left_output[line]} | {temperature_output[line]}")
        
        
    def start(self):
        while True:
            os.system("clear")
            print()
            self.print_all_usage()
            self.get_disk_strings()
            self.get_bytes_per_sec()
            time.sleep(1)

        

data = ComputerData()
data.start()
