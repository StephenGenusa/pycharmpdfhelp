import glob
import json
import os
import shutil
import sys
import time

import fitz
# https://www.selenium.dev/documentation/webdriver/
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with


class PyCharmHelpPDFBuilder:
    def __init__(self):
        self.hrefs_to_get = []
        self.menu_levels_info = {}
        self.document_version_number = ""
        self.pdf_download_path = os.path.join(os.getenv("USERPROFILE"), "Downloads")
        self.pdf_temp_path = os.path.join(self.pdf_download_path, "PyCharmPDFs")
        if not os.path.isdir(self.pdf_temp_path):
            os.makedirs(self.pdf_temp_path)
        self.pdf_counter = 0
        self.total_pdfs_expected = 0
        self.driver = None

    def setup_selenium_chrome(self):
        chrome_options = webdriver.ChromeOptions()
        settings = {
            "recentDestinations": [
                {
                    "id": "Save as PDF",
                    "origin": "local",
                    "account": "",
                }
            ],
            "selectedDestinationId": "Save as PDF",
            "version": 2,
            "isHeaderFooterEnabled": False,
            "scalingType": 3,
            "scaling": "85",
        }
        prefs = {
            "printing.print_preview_sticky_settings.appState": json.dumps(settings)
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--kiosk-printing")
        # Note: The ToC is automatically hidden if the browser window is too small
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(
            service=Service("chromedriver.exe"), options=chrome_options
        )

    def get_url(self, url_to_get):
        self.driver.get(url_to_get)
        time.sleep(1.5)

    def check_for_existing_pdf_files(self):
        """
        Test for PyCharm downloads and exit if found so that manual cleanup can be done. File numbering can
        be confused if old files are left hanging around
        """
        if glob.glob(self.pdf_download_path + "/*_ PyCharm.pdf"):
            print(
                f"I found _ PyCharm.pdf files in the download path {self.pdf_download_path}"
            )
            print(
                "Terminating. Please clean _ PyCharm.pdf files out directory so that files can be numbered properly"
            )
            sys.exit()

    def move_and_rename_file(self):
        """
        Move downloaded file. Code written to handle multiple files but there should be only one found
        """
        pdf_file_list = glob.glob(self.pdf_download_path + "/*_ PyCharm.pdf")
        for pdf_filename in pdf_file_list:
            new_pdf_filename = os.path.join(
                self.pdf_temp_path,
                str(self.pdf_counter + 1).zfill(4)
                + "_"
                + os.path.basename(pdf_filename),
            )
            shutil.move(pdf_filename, new_pdf_filename)
            self.pdf_counter += 1

    def get_latest_document_version_number(self):
        print("Getting version number of latest PyCharm help")
        self.get_url("https://www.jetbrains.com/help/pycharm/installation-guide.html")
        self.document_version_number = self.driver.find_elements(
            By.TAG_NAME, "div.dropdown__label"
        )[0].text

    def close_all_help_document_menus(self):
        print("Closing menus to determine tree hierarchy for bookmarks")
        for _ in range(7):
            menu_svg_elements = self.driver.find_elements(By.TAG_NAME, "svg")
            for menu_svg in menu_svg_elements:
                try:
                    svg_classname = menu_svg.get_attribute("class")
                    if (
                        svg_classname
                        and "toc-icon" in svg_classname
                        and "toc-icon--opened" in svg_classname
                    ):
                        menu_svg.click()
                except:
                    pass
                time.sleep(0.01)

    def expand_next_level_document_menus(self):
        # Expand menus so that the DOM elements are generated
        menu_svg_elements = self.driver.find_elements(By.TAG_NAME, "svg")
        for menu_svg in menu_svg_elements:
            svg_classname = menu_svg.get_attribute("class")
            if (
                svg_classname
                and "toc-icon" in svg_classname
                and "toc-icon--opened" not in svg_classname
            ):
                menu_svg.click()
                time.sleep(0.01)

    def build_list_of_urls(self):
        """
        Get all the hrefs that belong to the help document
        """
        print("Building a list of urls required to build PDF...")
        toc_element = self.driver.find_elements(By.XPATH, '//*[@id="webhelp-root"]')
        href_elements = toc_element[0].find_elements(By.XPATH, ".//*/a[@href]")
        for href_element in href_elements:
            href_value = href_element.get_attribute("href")
            if href_value and "/help" in href_value and "#" not in href_value:
                self.hrefs_to_get.append(href_value)
            if self.hrefs_to_get and (
                "/help" not in href_value or "sending-feedback" in href_value
            ):
                break
        self.total_pdfs_expected = len(self.hrefs_to_get)

    def build_url_level_list(self):
        print("Building help hierarchy for bookmarks")
        self.close_all_help_document_menus()
        print("Opening menus to determine tree hierarchy for bookmarks")
        for idx in range(7):
            li_elements = self.driver.find_elements(
                By.XPATH, '//*[@id="webhelp-root"]/div/div/nav/div/div/ul/li'
            )
            for li_element in li_elements:
                href_elements = li_element.find_elements(By.XPATH, "a[@href]")
                for href_element in href_elements:
                    if (
                        href_element.get_attribute("href")
                        not in self.menu_levels_info.keys()
                    ):
                        self.menu_levels_info[href_element.get_attribute("href")] = (
                            idx + 1
                        )
            self.expand_next_level_document_menus()

    def get_pycharm_section_pdf_filenames(self):
        """
        Gets all the existing PDF documents that have been download, renamed and moved to our temp location
        """
        return glob.glob(self.pdf_temp_path + "/*.pdf")

    def get_already_retrieved_url_count(self):
        self.pdf_counter = len(self.get_pycharm_section_pdf_filenames())

    def build_single_page(self, href_to_get, page_idx, total_page_count):
        print(f"Building PDF {page_idx}/{total_page_count} for {href_to_get}")
        self.get_url(href_to_get)
        self.driver.execute_script("window.print();")
        time.sleep(1)
        self.move_and_rename_file()

    def build_section_pdfs(self):
        total_page_count = len(self.hrefs_to_get) - self.pdf_counter
        print(f"Retrieving {total_page_count} URLs to build manual. Please wait...")
        for idx, href_value in enumerate(self.hrefs_to_get[self.pdf_counter :]):
            self.build_single_page(href_value, idx + 1, total_page_count)

    def verify_file_sizes(self):
        """
        Prior to building final PDF, test file size of everything retrieved and re-get any documents that failed
        to build properly the first time
        """
        pdf_filelist = self.get_pycharm_section_pdf_filenames()
        list_of_pages_to_get_again = [
            int(os.path.basename(pdf_filename)[0:4]) - 1
            for pdf_filename in pdf_filelist
            if os.path.getsize(pdf_filename) < 5000
        ]
        for file_number in list_of_pages_to_get_again:
            self.pdf_counter = file_number
            self.build_single_page(
                self.hrefs_to_get[file_number],
                file_number,
                len(list_of_pages_to_get_again),
            )
        self.driver.quit()

    def get_pdf_bookmark_name_from_filename(self, pdf_filename):
        """
        Get PDF bookmark name from the PDF file name
        """
        return os.path.basename(pdf_filename)[5:-14]

    def compile_pdfs_into_master(self):
        """
        Builds final PDF document
        """
        pdf_filelist = self.get_pycharm_section_pdf_filenames()
        if len(pdf_filelist) == self.total_pdfs_expected:
            pdf_filelist.sort()
            output_pdf = fitz.open()
            pdf_toc = []
            page_num = 1
            for idx, pdf_filename in enumerate(pdf_filelist):
                if self.hrefs_to_get[idx] in self.menu_levels_info.keys():
                    toc_level = self.menu_levels_info[self.hrefs_to_get[idx]]
                else:
                    toc_level = 1
                pdf_toc.append(
                    [
                        toc_level,
                        self.get_pdf_bookmark_name_from_filename(pdf_filename),
                        page_num,
                    ]
                )
                # TODO: Fixup web links to internal documentation
                with fitz.open(pdf_filename) as mfile:
                    output_pdf.insert_pdf(mfile)
                    page_num += mfile.pageCount
                    mfile.close()
            output_pdf.set_toc(pdf_toc)
            pdf_output_filename = os.path.join(self.pdf_download_path,
                                               "PyCharm_" + self.document_version_number + "_Documentation.pdf")
            output_pdf.save(pdf_output_filename)
            print("Process complete")
            os.startfile(pdf_output_filename)
        else:
            print(
                f"PDF count in {self.pdf_temp_path} does not match expected count of {self.total_pdfs_expected}"
            )

    def build_pycharm_help_pdf(self):
        self.check_for_existing_pdf_files()
        self.setup_selenium_chrome()
        self.get_latest_document_version_number()
        self.get_url(
            "https://www.jetbrains.com/help/pycharm/"
            + self.document_version_number
            + "/quick-start-guide.html"
        )
        self.build_url_level_list()
        self.build_list_of_urls()
        self.get_already_retrieved_url_count()
        self.build_section_pdfs()
        self.verify_file_sizes()
        self.compile_pdfs_into_master()


def main():
    pdf_builder = PyCharmHelpPDFBuilder()
    pdf_builder.build_pycharm_help_pdf()


if __name__ == "__main__":
    main()
