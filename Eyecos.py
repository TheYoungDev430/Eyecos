import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QToolBar, QLineEdit, QPushButton, QFileDialog, QListWidget,
    QDialog, QDialogButtonBox, QProgressDialog, QMessageBox, QAction
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt

class BrowserTab(QWidget):
    def __init__(self, url="https://www.google.com", download_callback=None):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl(url))
        self.layout.addWidget(self.browser)

        if download_callback:
            self.browser.page().profile().downloadRequested.connect(download_callback)

class BookmarksDialog(QDialog):
    def __init__(self, bookmarks, open_callback):
        super().__init__()
        self.setWindowTitle("Bookmarks")
        self.resize(400, 300)
        self.layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for title, url in bookmarks:
            self.list_widget.addItem(f"{title} - {url}")
        self.layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)

        self.list_widget.itemDoubleClicked.connect(lambda item: open_callback(item.text().split(" - ")[1]))
        buttons.accepted.connect(lambda: open_callback(self.get_selected_url()))

    def get_selected_url(self):
        item = self.list_widget.currentItem()
        if item:
            return item.text().split(" - ")[1]
        return None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eyecos")
        self.setGeometry(100, 100, 1200, 800)

        self.bookmarks = []

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)

        go_btn = QPushButton("Go")
        go_btn.clicked.connect(self.navigate_to_url)
        self.toolbar.addWidget(go_btn)

        new_tab_action = QAction("New Tab", self)
        new_tab_action.triggered.connect(lambda: self.add_new_tab("https://www.google.com"))
        self.toolbar.addAction(new_tab_action)

        bookmark_action = QAction("Bookmark Page", self)
        bookmark_action.triggered.connect(self.add_bookmark)
        self.toolbar.addAction(bookmark_action)

        show_bookmarks_action = QAction("Show Bookmarks", self)
        show_bookmarks_action.triggered.connect(self.show_bookmarks)
        self.toolbar.addAction(show_bookmarks_action)

        self.add_new_tab("https://www.google.com")

    def add_new_tab(self, url):
        new_tab = BrowserTab(url, self.handle_download)
        i = self.tabs.addTab(new_tab, "New Tab")
        self.tabs.setCurrentIndex(i)
        new_tab.browser.urlChanged.connect(lambda url: self.update_url_bar(url, i))
        new_tab.browser.titleChanged.connect(lambda title: self.tabs.setTabText(i, title))

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        current_tab = self.tabs.currentWidget()
        current_tab.browser.setUrl(QUrl(url))

    def update_url_bar(self, url, index):
        if index == self.tabs.currentIndex():
            self.url_bar.setText(url.toString())

    def handle_download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if path:
            download.setPath(path)
            download.accept()

            progress_dialog = QProgressDialog("Downloading...", "Cancel", 0, 100, self)
            progress_dialog.setWindowTitle("Download Progress")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.show()

            download.downloadProgress.connect(
                lambda received, total: progress_dialog.setValue(int(received * 100 / total) if total > 0 else 0)
            )

            def on_finished():
                progress_dialog.setValue(100)
                progress_dialog.close()
                QMessageBox.information(
                    self,
                    "Download Complete",
                    f"File downloaded to:\n{download.path()}"
                )

            download.finished.connect(on_finished)

    def add_bookmark(self):
        current_tab = self.tabs.currentWidget()
        title = self.tabs.tabText(self.tabs.currentIndex())
        url = current_tab.browser.url().toString()
        self.bookmarks.append((title, url))

    def show_bookmarks(self):
        dialog = BookmarksDialog(self.bookmarks, self.open_bookmark)
        dialog.exec()

    def open_bookmark(self, url):
        if url:
            self.add_new_tab(url)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
