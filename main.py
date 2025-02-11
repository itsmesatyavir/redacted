from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from colorama import *
from datetime import datetime
from fake_useragent import FakeUserAgent
import asyncio, base64, json, os, pytz
from aiohttp_socks import ProxyConnector

wib = pytz.timezone('Asia/Jakarta')

class RedactedAirways:
    def __init__(self) -> None:
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://quest.redactedairways.com/home',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}RedactedAirways Quests - BOT {Fore.YELLOW + Style.BRIGHT} Tool Shared By FOREST ARMY  (https://t.me/forestarmy) NO SELLING NO SPAM
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/itsmesatyavir/freeproxy/main/freeproxy
") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, address):
        if address not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[address] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[address]

    def rotate_proxy_for_account(self, address):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[address] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def print_question(self):
        while True:
            try:
                print("1. Run With Free Proxy ")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Free Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

    def decode_token(self, token: str):
        try:
            header, payload, signature = token.split(".")
            decoded_payload = base64.urlsafe_b64decode(payload + "==").decode("utf-8")
            parsed_payload = json.loads(decoded_payload)
            username = parsed_payload.get("user_name", "Unknown")

            return username
        except Exception as e:
            return None
        
    def save_new_token(self, old_token, new_token):
        file_path = 'tokens.txt'
        with open(file_path, 'r') as file:
            tokens = [line.strip() for line in file if line.strip()]
        
        updated_tokens = [new_token if token == old_token else token for token in tokens]

        with open(file_path, 'w') as file:
            file.write("\n".join(updated_tokens) + "\n")

    async def revalidate_token(self, token: str,proxy=None, retries=5):
        url = 'https://quest.redactedairways.com/ecom-gateway/revalidate'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Origin': 'https://quest.redactedairways.com',
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector,timeout=ClientTimeout(total=20)) as session:
                    async with session.post(url=url, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["token"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
        
    async def user_auth(self, token: str,proxy=None, retries=5):
        url = 'https://quest.redactedairways.com/ecom-gateway/auth'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}'
        }
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=20)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        if response.status == 401:
                            return None
                        
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
        
    async def user_info(self, token: str,proxy=None, retries=5):
        url = 'https://quest.redactedairways.com/ecom-gateway/user/info'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}'
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector,timeout=ClientTimeout(total=20)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["userData"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
            
    async def task_lists(self, token: str, type: str,proxy=None, retries=5):
        url = f'https://quest.redactedairways.com/ecom-gateway/{type}'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}'
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector,timeout=ClientTimeout(total=20)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
        
    async def complete_basic_tasks(self, token: str, task_id: str, task: dict,proxy=None, retries=5):
        url = f'https://quest.redactedairways.com/ecom-gateway/task/{task["task_action"]}'
        if "tweet_id" in task and task["tweet_id"]:
            key = "tweetId"
            action_id = task["tweet_id"]
        elif "twitter_id" in task and task["twitter_id"]:
            key = "twitterId"
            action_id = task["twitter_id"]
        else:
            return None

        data = json.dumps({"taskId":task_id, key:action_id})
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector,timeout=ClientTimeout(total=20)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
        
    async def complete_partner_tasks(self, token: str, task_id: str, task_type: str,proxy=None, retries=5):
        url = 'https://quest.redactedairways.com/ecom-gateway/partnerActivity'
        data = json.dumps({'partnerId':task_id, 'taskType':task_type})
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector,timeout=ClientTimeout(total=20)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
        
    async def process_accounts(self, token: str,username:str, use_proxy):
        proxy = self.get_next_proxy_for_account(username) if use_proxy else None
        new_token = None

        is_valid = await self.user_auth(token,proxy)
        if not is_valid:
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Status       :{Style.RESET_ALL}"
                f"{Fore.RED + Style.BRIGHT} Token Expired {Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT} Revalidating... {Style.RESET_ALL}"
            )

            new_token = await self.revalidate_token(token,proxy)
            if not new_token:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status       :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Revalidate Token Failed {Style.RESET_ALL}"
                )
                return
            
            self.save_new_token(token, new_token)
            
            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Status       :{Style.RESET_ALL}"
                f"{Fore.GREEN + Style.BRIGHT} Revalidate Token Success {Style.RESET_ALL}"
            )

        active_token = new_token if new_token else token
            
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Status       :{Style.RESET_ALL}"
            f"{Fore.GREEN + Style.BRIGHT} Token Active {Style.RESET_ALL}"
        )

        balance = "N/A"

        user = await self.user_info(active_token,proxy)
        if user:
            balance = user.get("overall_score", 0)

        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Balance      :{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {balance} Points {Style.RESET_ALL}"
        )

        for type in ["task/list", "partners"]:
            task_lists = await self.task_lists(active_token, type ,proxy)

            if task_lists:
                if type == "task/list":
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Basic Tasks  :{Style.RESET_ALL}"
                    )

                    tasks = task_lists.get("list", [])
                    for task in tasks:
                        if task:
                            task_id = task.get("_id")
                            title = task.get("task_name")
                            description = task.get("task_description")
                            reward = task.get("task_points")
                            is_completed = task.get("completed")

                            if task_id == "66df13c6fa429bb5c00ece79" and not is_completed:
                                self.log(
                                    f"{Fore.MAGENTA + Style.BRIGHT}      ->{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} {title} {Style.RESET_ALL}"
                                    f"{Fore.YELLOW + Style.BRIGHT}Skipped{Style.RESET_ALL}"
                                )
                                continue

                            elif is_completed:
                                continue

                            complete = await self.complete_basic_tasks(active_token, task_id, task ,proxy)
                            if complete:
                                self.log(
                                    f"{Fore.MAGENTA + Style.BRIGHT}      ->{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} {title} {Style.RESET_ALL}"
                                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} {description} {Style.RESET_ALL}"
                                    f"{Fore.GREEN + Style.BRIGHT}Completed{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                                    f"{Fore.CYAN + Style.BRIGHT}Reward{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} {reward} Points {Style.RESET_ALL}"
                                )
                            else:
                                self.log(
                                    f"{Fore.MAGENTA + Style.BRIGHT}      ->{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} {title} {Style.RESET_ALL}"
                                    f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
                                    f"{Fore.WHITE + Style.BRIGHT} {description} {Style.RESET_ALL}"
                                    f"{Fore.RED + Style.BRIGHT}Not Completed{Style.RESET_ALL}"
                                )
                            await asyncio.sleep(5)
                                
                elif type == "partners":
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}Partner Tasks:{Style.RESET_ALL}"
                    )

                    tasks = task_lists.get("data", [])
                    for task in tasks:
                        if task:
                            task_id = task.get("_id")
                            group_title = task.get("partner_name")

                            self.log(
                                f"{Fore.MAGENTA + Style.BRIGHT}   ●{Style.RESET_ALL}"
                                f"{Fore.GREEN + Style.BRIGHT} {group_title} {Style.RESET_ALL}"
                            )

                            sub_task_lists = task.get("tasks", [])
                            for sub_task in sub_task_lists:
                                if sub_task:
                                    task_type = sub_task.get("task_type")
                                    title = sub_task.get("text")
                                    reward = sub_task.get("points")
                                    status = sub_task.get("status")

                                    if status == "completed":
                                        continue

                                    complete = await self.complete_partner_tasks(active_token, task_id, task_type,proxy)
                                    if complete:
                                        self.log(
                                            f"{Fore.MAGENTA + Style.BRIGHT}      ->{Style.RESET_ALL}"
                                            f"{Fore.WHITE + Style.BRIGHT} {title} {Style.RESET_ALL}"
                                            f"{Fore.GREEN + Style.BRIGHT}Completed{Style.RESET_ALL}"
                                            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                                            f"{Fore.CYAN + Style.BRIGHT}Reward{Style.RESET_ALL}"
                                            f"{Fore.WHITE + Style.BRIGHT} {reward} Points {Style.RESET_ALL}"
                                        )
                                    else:
                                        self.log(
                                            f"{Fore.MAGENTA + Style.BRIGHT}      ->{Style.RESET_ALL}"
                                            f"{Fore.WHITE + Style.BRIGHT} {title} {Style.RESET_ALL}"
                                            f"{Fore.RED + Style.BRIGHT}Not Completed{Style.RESET_ALL}"
                                        )
                                    await asyncio.sleep(5)

            else:
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Task    Lists:{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} Data Is None {Style.RESET_ALL}"
                )
                
    async def main(self):
        try:
            with open('tokens.txt', 'r') as file:
                tokens = [line.strip() for line in file if line.strip()]

            use_proxy_choice = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True
            
            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(tokens)}{Style.RESET_ALL}"
                )

                separator = "=" * 25
                for token in tokens:
                    if token:
                        username = self.decode_token(token)
                        if username:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                                f"{Fore.WHITE + Style.BRIGHT} {username} {Style.RESET_ALL}"
                                f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                            )
                            await self.process_accounts(token,username, use_proxy)
                            await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*60)
                seconds = 12 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'tokens.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = RedactedAirways()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] RedactedAirways Quests - BOT{Style.RESET_ALL}                                       "                              
        )