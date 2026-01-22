import threading
import time
import random
import queue  # مكتبة تنظيم الدور
import customtkinter as ctk
from tkinter import messagebox, filedialog
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class TinChatBot(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gomeet Bot (Final Actions Added)")
        self.geometry("450x800")
        self.resizable(False, False)

        self.accounts = []
        self.account_queue = queue.Queue()
        self.is_running = False
        self.fixed_password = ""
        self.lock = threading.Lock()

        self.label = ctk.CTkLabel(self, text="Gomeet Auto (Fixed Password)", font=("Arial", 20, "bold"))
        self.label.pack(pady=15)

        # 1. زر تحميل الإيميلات
        self.btn_load = ctk.CTkButton(self, text="📁 Load Emails Only (.txt)", command=self.load_file, width=300,
                                      height=40)
        self.btn_load.pack(pady=10)

        self.lbl_count = ctk.CTkLabel(self, text="No emails loaded", text_color="gray")
        self.lbl_count.pack(pady=5)

        # 2. حقل الباسورد الثابت
        self.label_pass = ctk.CTkLabel(self, text="Fixed Password for All Accounts:")
        self.label_pass.pack(pady=(10, 0))

        self.entry_pass = ctk.CTkEntry(self, width=200, placeholder_text="Enter Password", show="*")
        self.entry_pass.pack(pady=5)

        # 3. عدد التابات
        self.label_threads = ctk.CTkLabel(self, text="Number of Tabs (Threads):")
        self.label_threads.pack(pady=(10, 0))

        self.entry_threads = ctk.CTkEntry(self, width=100, placeholder_text="e.g. 3")
        self.entry_threads.pack(pady=5)
        self.entry_threads.insert(0, "1")

        # خيار الـ Matches
        self.do_matches_var = ctk.BooleanVar(value=True)
        self.matches_check = ctk.CTkCheckBox(self, text="Do 10 Matches (If 'Go')", variable=self.do_matches_var)
        self.matches_check.pack(pady=10)

        self.start_btn = ctk.CTkButton(self, text="🚀 Start Loop", command=self.start_main_thread, width=200,
                                       height=40, fg_color="green", state="disabled")
        self.start_btn.pack(pady=20)

        self.log_box = ctk.CTkTextbox(self, width=400, height=200)
        self.log_box.pack(pady=10)
        self.log_box.insert("end",
                            "1. Load .txt file (EMAILS ONLY)\n2. Enter Fixed Password\n3. Click Start\n\n")

    def log(self, message):
        with self.lock:
            try:
                self.log_box.insert("end", f"> {message}\n")
                self.log_box.see("end")
            except:
                pass

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.accounts = []
            for line in lines:
                email = line.strip()
                if email and "@" in email:
                    self.accounts.append(email)

            if self.accounts:
                self.lbl_count.configure(text=f"✅ Loaded {len(self.accounts)} emails", text_color="green")
                self.start_btn.configure(state="normal")
                self.log(f"Loaded {len(self.accounts)} emails.")
            else:
                messagebox.showerror("Error", "No valid emails found!")

    def start_main_thread(self):
        if not self.accounts:
            return

        self.fixed_password = self.entry_pass.get()
        if not self.fixed_password:
            messagebox.showwarning("Missing Password", "Please enter the Fixed Password first!")
            return

        try:
            num_threads = int(self.entry_threads.get())
            if num_threads < 1: num_threads = 1
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for tabs.")
            return

        self.is_running = True
        self.start_btn.configure(state="disabled", text="Running...")
        self.btn_load.configure(state="disabled")
        self.entry_pass.configure(state="disabled")

        self.account_queue = queue.Queue()
        for email in self.accounts:
            self.account_queue.put(email)

        t = threading.Thread(target=self.manage_workers, args=(num_threads,))
        t.daemon = True
        t.start()

    def manage_workers(self, num_threads):
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.worker_loop, args=(i + 1,))
            t.daemon = True
            t.start()
            threads.append(t)
            time.sleep(2)

        self.account_queue.join()

        self.log("✅ All tasks completed!")
        self.start_btn.configure(state="normal", text="🚀 Start Loop")
        self.btn_load.configure(state="normal")
        self.entry_pass.configure(state="normal")
        self.is_running = False

    def worker_loop(self, thread_id):
        while not self.account_queue.empty() and self.is_running:
            try:
                email = self.account_queue.get(timeout=3)
                password = self.fixed_password

                self.log(f"🔵 [Tab {thread_id}] Starting: {email}")
                self.run_single_account(email, password, thread_id)
                self.log(f"🏁 [Tab {thread_id}] Finished: {email}")

                self.account_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                self.log(f"❌ [Tab {thread_id}] Queue Error: {str(e)}")
                self.account_queue.task_done()

    def run_single_account(self, email, password, thread_id):
        driver = None
        try:
            options = uc.ChromeOptions()
            options.add_argument(f"--window-size=500,700")
            driver = uc.Chrome(options=options)
            prefs = {
                "profile.default_content_setting_values.geolocation": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.media_stream_mic": 2,
                "profile.default_content_setting_values.media_stream_camera": 2
            }
            options.add_experimental_option("prefs", prefs)

            driver = uc.Chrome(options=options, version_main=142)
            wait = WebDriverWait(driver, 20)

            # Login Flow
            driver.get("https://gomeet.today/")
            time.sleep(2)

            try:
                driver.execute_script("document.getElementById('rc-pop-cookie')?.remove();")
            except:
                pass
            # Login Button
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="home-landpage"]/div[1]/div[1]/div[4]/span[1]'))).click()
            time.sleep(1.5)
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div/div[2]/div/div[2]/div/button[4]'))).click()
            time.sleep(1.5)

            # Credentials
            email_field = wait.until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div/div[2]/div/div/div[1]/div/input')))
            email_field.clear()
            email_field.send_keys(email)
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div/div[2]/div/div/div[3]/div'))).click()
            time.sleep(1.5)

            pass_field = wait.until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div/div[2]/div/div/div[1]/div[1]/input')))
            pass_field.clear()
            pass_field.send_keys(password)
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div/div[2]/div/div/div[3]/button'))).click()

            time.sleep(3)

            # I Agree
            try:
                agree_btn = driver.find_element(By.XPATH,
                                                "//div[contains(@class, 'the-btn') and contains(., 'I agree')]")
                driver.execute_script("arguments[0].click();", agree_btn)
                time.sleep(1)
            except:
                pass

            # ==========================================================
            #  CHECK TASKS
            # ==========================================================
            should_continue = False
            try:
                task_icon_xpath = '//*[@id="side-body-wrap"]/div[2]/div[1]/div[2]/div/svg/g/path'
                task_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, task_icon_xpath)))
                driver.execute_script("arguments[0].click();", task_btn)
                time.sleep(2)

                try:
                    get_coins_btn = driver.find_element(By.XPATH, "//*[contains(text(), 'Get coins')]")
                    if get_coins_btn.is_displayed():
                        driver.execute_script("arguments[0].click();", get_coins_btn)
                        time.sleep(1)
                except:
                    pass

                try:
                    btn_1 = driver.find_element(By.XPATH,
                                                "(//div[contains(@class, 'task-item')]//div[contains(@class, 'btn')])[1]")
                    if "Claim" in btn_1.text:
                        driver.execute_script("arguments[0].click();", btn_1)
                        self.log(f"💰 [Tab {thread_id}] Claimed Login Reward")
                        time.sleep(1)
                except:
                    pass

                try:
                    btn_2 = driver.find_element(By.XPATH,
                                                "(//div[contains(@class, 'task-item')]//div[contains(@class, 'btn')])[2]")
                    btn_3 = driver.find_element(By.XPATH,
                                                "(//div[contains(@class, 'task-item')]//div[contains(@class, 'btn')])[3]")

                    if "Go" in btn_2.text or "Go" in btn_3.text:
                        should_continue = True
                    elif "Claim" in btn_2.text or "Claim" in btn_3.text:
                        should_continue = True
                    else:
                        self.log(f"🛑 [Tab {thread_id}] Tasks already done.")
                        # هنا يجب تنفيذ خطوات الخروج الأخيرة حتى لو المهام منتهية
                        self.perform_final_logout(driver, thread_id)
                        return

                except:
                    should_continue = True

                if should_continue:
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(1)
            except:
                pass

            # ==========================================================
            #  MATCHES
            # ==========================================================
            try:
                btns = driver.find_elements(By.XPATH,
                                            "//span[contains(text(), 'Get coins') or contains(text(), 'Claim')]")
                for btn in btns:
                    if btn.is_displayed(): driver.execute_script("arguments[0].click();", btn)
            except:
                pass

            if self.do_matches_var.get():
                self.log(f"🎯 [Tab {thread_id}] Matches...")
                try:
                    match_go = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH,
                                                                                          "//div[contains(text(), 'Match for')]/following-sibling::div//span[contains(text(), 'Go')]")))
                    driver.execute_script("arguments[0].click();", match_go)
                except:
                    pass

                time.sleep(2)
                for i in range(1, 15):
                    try:
                        start_btn = driver.find_element(By.XPATH,
                                                        '//*[@id="app-area"]/div[3]/div/div/div/div[1]/div/div[2]')
                        if start_btn.is_displayed(): driver.execute_script("arguments[0].click();", start_btn)
                    except:
                        pass
                    time.sleep(1)
                    try:
                        popups = driver.find_elements(By.XPATH, "//*[contains(@class, 'close')]")
                        for p in popups:
                            if p.is_displayed(): driver.execute_script("arguments[0].click();", p)
                        next_btns = driver.find_elements(By.XPATH,
                                                         "//*[contains(@class, 'btn-next') or contains(@class, 'icon-next')]")
                        clicked = False
                        for btn in next_btns:
                            if btn.is_displayed():
                                driver.execute_script("arguments[0].click();", btn)
                                clicked = True;
                                break
                        if not clicked:
                            heart = driver.find_element(By.XPATH, "//*[contains(@class, 'heart')]")
                            driver.execute_script("arguments[0].click();", heart)
                    except:
                        pass
                    time.sleep(0.5)

                try:
                    driver.back(); time.sleep(1.5)
                except:
                    pass

            # ==========================================================
            #  CHAT
            # ==========================================================
            self.log(f"💬 [Tab {thread_id}] Chat...")
            chat_icon_xpath = '//*[@id="app-area"]/div[4]/div[1]/ul[1]/li[5]'
            try:
                chat_icon = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, chat_icon_xpath)))
                driver.execute_script("arguments[0].click();", chat_icon)
                time.sleep(2)
            except:
                return

            selected_chat_element = None
            is_request_folder = False
            try:
                list_container = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'im-list')]")))
                all_chats = list_container.find_elements(By.XPATH, "./div")
                for chat in all_chats:
                    chat_text = chat.text
                    if not chat.is_displayed(): continue
                    if "TinChat Team" in chat_text: continue
                    if "New friend requests" in chat_text: selected_chat_element = chat; is_request_folder = True; break
                    if chat_text.strip(): selected_chat_element = chat; is_request_folder = False; break

                if selected_chat_element:
                    driver.execute_script("arguments[0].click();", selected_chat_element)
                    time.sleep(1.5)
                    if is_request_folder:
                        try:
                            req_tab = driver.find_element(By.XPATH, '//*[@id="u--4"]')
                            driver.execute_script("arguments[0].click();", req_tab);
                            time.sleep(1)
                            sub_chat = driver.find_element(By.XPATH, '//*[@id="app-area"]/div[5]/div/div[2]/div/div[1]')
                            driver.execute_script("arguments[0].click();", sub_chat);
                            time.sleep(1.5)
                        except:
                            pass

                    input_el = None
                    selectors = [(By.TAG_NAME, "textarea"), (By.TAG_NAME, "input"),
                                 (By.XPATH, "//div[@contenteditable='true']")]
                    for method, val in selectors:
                        try:
                            els = driver.find_elements(method, val)
                            for el in els:
                                if el.is_displayed(): input_el = el; break
                            if input_el: break
                        except:
                            pass
                    if input_el:
                        input_el.click();
                        input_el.send_keys("hi");
                        time.sleep(0.5)
                        try:
                            send_btn = driver.find_element(By.XPATH,
                                                           '//*[@id="app-area"]/div[5]/div/div[2]/div/div[2]/div[2]/div[1]/div[2]')
                            driver.execute_script("arguments[0].click();", send_btn)
                        except:
                            ActionChains(driver).send_keys(Keys.ENTER).perform()
            except:
                pass

            # ==========================================================
            #  FINAL CLAIMS
            # ==========================================================
            time.sleep(1.5)
            try:
                task_icon_xpath = '//*[@id="side-body-wrap"]/div[2]/div[1]/div/div'
                task_btn = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, task_icon_xpath)))
                driver.execute_script("arguments[0].click();", task_btn)
                time.sleep(2)
                for _ in range(5):
                    claims = driver.find_elements(By.XPATH,
                                                  "//span[contains(text(), 'Claim') or contains(text(), 'claim')]")
                    clicked = False
                    for btn in claims:
                        if btn.is_displayed():
                            try:
                                driver.execute_script("arguments[0].click();", btn)
                                self.log(f"🎉 [Tab {thread_id}] Final Claim!")
                                clicked = True;
                                time.sleep(1)
                            except:
                                pass
                    if not clicked: break
            except:
                pass

            # ==========================================================
            #  ⚡ NEW: PROFILE & LOGOUT ACTIONS
            # ==========================================================
            self.perform_final_logout(driver, thread_id)

        except Exception as e:
            self.log(f"❌ [Tab {thread_id}] Error: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def perform_final_logout(self, driver, thread_id):
        """دالة مساعدة لتنفيذ خطوات الخروج الأخيرة"""
        try:
            time.sleep(1.5)
            self.log(f"👤 [Tab {thread_id}] Clicking Profile...")
            profile_xpath = '//*[@id="side-body-wrap"]/div[2]/div[2]/div[1]/img'
            profile_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, profile_xpath)))
            driver.execute_script("arguments[0].click();", profile_btn)

            time.sleep(1.5)

            self.log(f"🔘 [Tab {thread_id}] Clicking Final Button...")
            final_btn_xpath = '//*[@id="app-area"]/div[3]/div/div/div[5]/div[1]/div/div[2]/div[3]/div'
            final_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, final_btn_xpath)))
            driver.execute_script("arguments[0].click();", final_btn)

            self.log(f"✅ [Tab {thread_id}] Final Actions Done.")
            time.sleep(2)
        except Exception as e:
            self.log(f"⚠️ [Tab {thread_id}] Final Action Error: {e}")


if __name__ == "__main__":
    app = TinChatBot()
    app.mainloop()
