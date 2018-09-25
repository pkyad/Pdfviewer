#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from subprocess import Popen
from PyQt4 import QtCore
from PyQt4.QtGui import (
    QApplication, QMainWindow, QPixmap, QImage, QWidget, QFrame, QVBoxLayout, QLabel,
    QFileDialog, QInputDialog, QAction, QIcon, QLineEdit, QStandardItem, QStandardItemModel,
    QIntValidator, QComboBox, QPainter, QColor, QMessageBox,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGroupBox, QHBoxLayout,
    QCalendarWidget, QGridLayout, QAbstractItemView, QScrollArea, QDateEdit, QTextEdit, QPalette, QPrinter
)
#from PyQt4.QtGui import QDesktopServices
from popplerqt4 import Poppler
import resources_rc
from ui_main_window import Ui_window
from __init__ import __version__

#from PyQt4 import uic
#main_ui = uic.loadUiType("main_window.ui")

DEBUG = False
SCREEN_DPI = 100
HOMEDIR = os.environ["HOME"]

#def pt2pixel(point, dpi):
#    return dpi*point/72.0

class Renderer(QtCore.QObject):
    rendered = QtCore.pyqtSignal(int, QImage)
    textFound = QtCore.pyqtSignal(int, QtCore.QRectF)

    def __init__(self, render_even_pages=True):
        QtCore.QObject.__init__(self)
        self.doc = None
        self.render_even_pages = render_even_pages
        self.painter = QPainter()
        self.link_color = QColor(0,0,127, 40)

    def render(self, page_no, dpi):
        """ render(int, float)
        This slot takes page no. and dpi and renders that page, then emits a signal with QImage"""
        # Returns when both is true or both is false
        if not ((page_no%2==0 and self.render_even_pages) or (page_no%2!=0 and self.render_even_pages==False)):
            return
        page = self.doc.page(page_no)
        if not page : return
        img = page.renderToImage(dpi, dpi)
        # Add Heighlight over Link Annotation
        self.painter.begin(img)
        annots = page.annotations()
        for annot in annots:
          if annot.subType() == Poppler.Annotation.ALink:
            x, y = annot.boundary().left()*img.width(), annot.boundary().top()*img.height()
            w, h = annot.boundary().width()*img.width()+1, annot.boundary().height()*img.height()+1
            self.painter.fillRect(x, y, w, h, self.link_color)
        self.painter.end()
        self.rendered.emit(page_no, img)

    def loadDocument(self, filename, password=''):
        """ loadDocument(str)
        Main thread uses this slot to load document for rendering """
        self.doc = Poppler.Document.load(filename, password, password)
        self.doc.setRenderHint(Poppler.Document.TextAntialiasing | Poppler.Document.TextHinting |
                               Poppler.Document.Antialiasing | 0x00000020 )

    def findText(self, text, page_num, area, find_reverse):
        if find_reverse:
          pages = range(page_num+1)
          pages.reverse()
          for page_no in pages:
            page = self.doc.page(page_no)
            found = page.search(text, area, Poppler.Page.PreviousResult, Poppler.Page.CaseInsensitive )
            if found:
              self.textFound.emit(page_no, area)
              break
            area = QtCore.QRectF(page.pageSizeF().width(), page.pageSizeF().height(),0,0) if find_reverse else QtCore.QRectF()
        else:
          pages = range(page_num, self.doc.numPages())
          for page_no in pages:
            page = self.doc.page(page_no)
            found = page.search(text, area, Poppler.Page.NextResult, Poppler.Page.CaseInsensitive )
            if found:
              self.textFound.emit(page_no, area)
              break
            area = QtCore.QRectF()


#class Main(main_ui[0], main_ui[1]):
class Main(QMainWindow, Ui_window):
    renderRequested = QtCore.pyqtSignal(int, float)
    loadFileRequested = QtCore.pyqtSignal(unicode, QtCore.QByteArray)
    findTextRequested = QtCore.pyqtSignal(str, int, QtCore.QRectF, bool)

    def __init__(self,parent = None):
        # Second.__init__(self)
        super(Main, self).__init__(parent)
        self.setupUi(self)
        self.dockSearch.hide()
        self.dockWidget.hide()
        self.dockWidget.setMinimumWidth(250)
        self.findTextEdit.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.treeView.setAlternatingRowColors(True)
        self.treeView.clicked.connect(self.onOutlineClick)
        self.first_document = True
        desktop = QApplication.desktop()
        self.resize_page_timer = QtCore.QTimer(self)
        self.resize_page_timer.setSingleShot(True)
        self.resize_page_timer.timeout.connect(self.onWindowResize)
        # Add shortcut actions
        self.firstPageAction = QAction(QIcon(":/go-first.png"), "First Page", self)
        self.firstPageAction.triggered.connect(self.goFirstPage)
        self.lastPageAction = QAction(QIcon(":/go-last.png"), "Last Page", self)
        self.lastPageAction.triggered.connect(self.goLastPage)
        self.gotoPageAction = QAction(QIcon(":/goto.png"), "GoTo Page", self)
        self.gotoPageAction.triggered.connect(self.gotoPage)
        self.copyTextAction = QAction(QIcon(":/copy.png"), "Copy Text", self)
        self.copyTextAction.setCheckable(True)
        self.copyTextAction.triggered.connect(self.toggleCopyText)
        self.findTextAction = QAction(QIcon(":/search.png"), "Find Text", self)
        self.findTextAction.setShortcut('Ctrl+F')
        self.findTextAction.triggered.connect(self.dockSearch.show)
        self.openFileAction.triggered.connect(self.openFile)


        self.quitAction.triggered.connect(self.close)
        self.toPSAction.triggered.connect(self.exportToPS)
        self.docInfoAction.triggered.connect(self.docInfo)
        self.zoominAction.triggered.connect(self.zoomIn)
        self.zoomoutAction.triggered.connect(self.zoomOut)
        self.prevPageAction.triggered.connect(self.goPrevPage)
        self.nextPageAction.triggered.connect(self.goNextPage)
        self.undoJumpAction.triggered.connect(self.undoJump)
        # Create widgets for menubar / toolbar
        self.gotoPageEdit = QLineEdit(self)
        self.gotoPageEdit.setPlaceholderText("Jump to page...")
        self.gotoPageEdit.setMaximumWidth(120)
        self.gotoPageEdit.returnPressed.connect(self.gotoPage)
        self.gotoPageValidator = QIntValidator(1,1, self.gotoPageEdit)
        self.gotoPageEdit.setValidator(self.gotoPageValidator)
        self.pageNoLabel = QLabel(self)
        self.pageNoLabel.setFrameShape(QFrame.StyledPanel)
        spacer = QWidget(self)
        spacer.setSizePolicy(1|2|4,1|4)
        self.zoomLevelCombo = QComboBox(self)
        self.zoomLevelCombo.addItems(["Fixed Width", "75%", "90%","100%","110%","121%","133%","146%", "175%", "200%","300%","400%"])
        self.zoomLevelCombo.activated.connect(self.setZoom)
        self.zoom_levels = [0, 75, 90, 100, 110 , 121, 133, 146, 175, 200, 300, 400]
        # Add toolbar actions
        self.toolBar.addAction(self.openFileAction)

        self.toolBar.addSeparator()
        self.toolBar.addAction(self.zoomoutAction)
        self.toolBar.addWidget(self.zoomLevelCombo)
        self.toolBar.addAction(self.zoominAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.firstPageAction)
        self.toolBar.addAction(self.prevPageAction)
        self.toolBar.addWidget(self.pageNoLabel)
        self.toolBar.addAction(self.nextPageAction)
        self.toolBar.addAction(self.lastPageAction)
        self.toolBar.addAction(self.undoJumpAction)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.gotoPageEdit)
        self.toolBar.addAction(self.gotoPageAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.copyTextAction)
        self.toolBar.addAction(self.findTextAction)
        self.toolBar.addWidget(spacer)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.quitAction)
        # Add widgets
        # Impoort settings
        self.settings = QtCore.QSettings("gospel-pdf", "main", self)
        self.recent_files = list( self.settings.value("RecentFiles", []).toStringList())
        self.history_filenames = list( self.settings.value("HistoryFileNameList", []).toStringList())
        self.history_page_no = list( self.settings.value("HistoryPageNoList", []).toStringList() )
        self.offset_x = int(self.settings.value("OffsetX", 4).toString())
        self.offset_y = int(self.settings.value("OffsetY", 26).toString())
        self.available_area = [desktop.availableGeometry().width(), desktop.availableGeometry().height()]
        self.zoomLevelCombo.setCurrentIndex(int(self.settings.value("ZoomLevel", 2).toString()))
        # Connect Signals
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.onMouseScroll)
        self.scrollArea.verticalScrollBar().sliderReleased.connect(self.onSliderRelease)
        self.findTextEdit.returnPressed.connect(self.findNext)
        self.findNextButton.clicked.connect(self.findNext)
        self.findBackButton.clicked.connect(self.findBack)
        self.findCloseButton.clicked.connect(self.dockSearch.hide)
        self.dockSearch.visibilityChanged.connect(self.toggleFindMode)
        # Create separate thread and move renderer to it
        self.thread1 = QtCore.QThread(self)
        self.renderer1 = Renderer()
        self.renderer1.moveToThread(self.thread1) # this must be moved before connecting signals
        self.renderRequested.connect(self.renderer1.render)
        self.loadFileRequested.connect(self.renderer1.loadDocument)
        self.findTextRequested.connect(self.renderer1.findText)
        self.renderer1.rendered.connect(self.setRenderedImage)
        self.renderer1.textFound.connect(self.onTextFound)
        self.thread1.start()
        self.thread2 = QtCore.QThread(self)
        self.renderer2 = Renderer(False)
        self.renderer2.moveToThread(self.thread2)
        self.renderRequested.connect(self.renderer2.render)
        self.loadFileRequested.connect(self.renderer2.loadDocument)
        self.renderer2.rendered.connect(self.setRenderedImage)
        self.thread2.start()
        # Initialize Variables
        self.filename = ''
        self.current_page = 0
        self.pages = []
        self.jumped_from = None
        self.max_preload = 1
        self.recent_files_actions = []
        self.addRecentFiles()

        self.commentsLayout = QGridLayout()  # --------------Another Grid layout--------

        self.commentsTable = QTableWidget() #---------craeting comment table------
        self.commentsTable.setColumnCount(2)
        self.commentsTable.setRowCount(4)
        self.commentsTable.setHorizontalHeaderLabels(QtCore.QString(";User").split(";"))
        self.commentsTable.horizontalHeader().setStretchLastSection(True)
        self.commentsTable.verticalHeader().hide()
        self.commentsTable.setColumnWidth(0,50)
        self.commentsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.commentsTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.commentsViewTable = QTableWidget() #------------creating Another comment table----
        self.commentsViewTable.setColumnCount(2)
        self.commentsViewTable.setRowCount(4)

        self.commentsViewTable.setHorizontalHeaderLabels(QtCore.QString(";Comment").split(";"))
        self.commentsViewTable.horizontalHeader().setStretchLastSection(True)
        self.commentsViewTable.verticalHeader().hide()
        self.commentsViewTable.setColumnWidth(0,50)
        self.commentsViewTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.commentsViewTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.commentsViewTable.setMinimumHeight(600)
        self.commentsLayout.addWidget(self.commentsTable ,0,0,QtCore.Qt.AlignTop ) #----------adding table to the layout
        self.commentsLayout.addWidget(self.commentsViewTable ,2,0,QtCore.Qt.AlignBottom)
        self.commentsLayout.setRowMinimumHeight(0,150)
        self.commentsLayout.setRowMinimumHeight(1,10)
        #self.commentsLayout.setRowStretch(0,2)
        #self.commentsLayout.setRowStretch(1,3)
        # self.commentsTable.setStretch(0, 1)
        self.commentsLayout.setHorizontalSpacing(2)

        self.commentsWidget = QWidget()
        self.commentsWidget.setMaximumWidth(300)
        self.commentsWidget.setLayout(self.commentsLayout)


        self.table = QTableWidget()
        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(QtCore.QString("Page;Document Title;Text").split(";"))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setColumnWidth(0,50)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.table.setRowCount(18)

        self.table.setMinimumHeight(600)


        #gbSearch = QGroupBox('Search..')
        # self.pageNavigratorSearch = QHBoxLayout() #create Horizontal Box layout

        self.pageNavigratorSearch = QGridLayout()

        self.searchText =  QLineEdit("")
        self.searchText.setPlaceholderText("Search Here...")

        self.searchBtn = QPushButton('Search') #search btn


        self.date1 = QDateEdit()
        self.date1.setDisplayFormat('dd/MM/yyyy')
        self.date1.setCalendarPopup(True)
        self.date1.setDate(QtCore.QDate.currentDate())


        self.date2 = QDateEdit()
        self.date2.setDisplayFormat('dd/MM/yyyy')
        self.date2.setCalendarPopup(True)
        self.date2.setDate(QtCore.QDate.currentDate())

        self.fromLbl = QLabel("From")
        self.fromLbl.setStyleSheet("font: bold 30ft AGENTORANGE")
        self.toLbl = QLabel("To")
        self.toLbl.setStyleSheet("font: bold 30ft AGENTORANGE")

        # self.pageNavigratorSearch1 = QHBoxLayout()

        self.pageNavigratorSearch.addWidget(self.searchText,0,0,1,3)
        self.pageNavigratorSearch.addWidget(self.fromLbl,1,0)
        self.pageNavigratorSearch.addWidget(self.toLbl,1,1)
        self.pageNavigratorSearch.addWidget(self.date1,2,0) #add cal cal2 and button to horizontal layout
        self.pageNavigratorSearch.addWidget(self.date2,2,1)
        self.pageNavigratorSearch.addWidget(self.searchBtn,2,2)

        self.pageNavigratorSearch.setRowMinimumHeight(0,40)
        self.pageNavigratorSearch.setRowMinimumHeight(1,50)
        self.pageNavigratorSearch.setRowMinimumHeight(2,5)


        # self.pageNavigratorSearch.setRowStretch(2,1)

        # self.pageNavigratorSearch.setRowMinimumHeight(0,1)
        # self.pageNavigratorSearch.setRowMinimumHeight(1,20)
        # self.pageNavigratorSearch.setRowMinimumHeight(2,20)



        #gbSearch.setLayout(self.pageNavigratorSearch)

        self.configureLayout = QGridLayout()      #------Another grid layout----------
        #self.configureLayout.addWidget(self.searchText , 0, 0) #----adding line edit to layout
        #self.configureLayout.addWidget(gbSearch , 0, 0) #-------adding gbsearch groupbox to layout
        #self.configureLayout.addWidget(self.searchBtn,2,0)

        self.configureLayout.addLayout(self.pageNavigratorSearch,0,0,QtCore.Qt.AlignTop)

        self.configureLayout.addWidget(self.table ,1,0,2,0,QtCore.Qt.AlignBottom) #--------adding table to layout-----

        self.configureLayout.setRowMinimumHeight(0,160)
        self.configureLayout.setRowMinimumHeight(1,10)

        #self.configureLayout.setRowMinimumHeight(2,10)
        self.configureLayout.setHorizontalSpacing(2)

        self.configureWidget = QWidget()
        self.configureWidget.setMaximumWidth(550)
        self.configureWidget.setLayout(self.configureLayout)

        self.verticalLayout_2.addWidget(self.commentsWidget,0,1)
        self.verticalLayout_2.addWidget(self.configureWidget,0,2)


        #self.verticalLayout_2.addWidget(self.dockWidget,1,0)

        #self.verticalLayout_2.setColumnStretch(0,5)
        self.verticalLayout_2.setColumnStretch(1,1)
        #self.verticalLayout_2.setColumnStretch(2,1)
        self.verticalLayout_2.setColumnMinimumWidth(0,720)
        self.verticalLayout_2.setColumnMinimumWidth(1,50)
        self.verticalLayout_2.setColumnMinimumWidth(2,0)


        # Show Window
        width = int(self.settings.value("WindowWidth").toString())
        height = int(self.settings.value("WindowHeight").toString())
        #width = 1300
        #height = 900
        self.resize(width, height)
        # self.show()
        self.showMaximized()

    def addRecentFiles(self):
        self.recent_files_actions[:] = []
        self.menuRecentFiles.clear()
        for each in self.recent_files:
            name = elideMiddle(os.path.basename(unicode(each)), 60)
            action = self.menuRecentFiles.addAction(name, self.openRecentFile)
            self.recent_files_actions.append(action)
        self.menuRecentFiles.addSeparator()
        self.menuRecentFiles.addAction(QIcon(':/edit-clear.png'), 'Clear Recents', self.clearRecents)

    def openRecentFile(self):
        action = self.sender()
        index = self.recent_files_actions.index(action)
        self.loadPDFfile(self.recent_files[index])

    def clearRecents(self):
        self.recent_files_actions[:] = []
        self.menuRecentFiles.clear()
        self.recent_files[:] = []

    def removeOldDoc(self):
        # Save current page number
        self.saveFileData()
        # Remove old document
        for i in range(len(self.pages)):
            self.verticalLayout.removeWidget(self.pages[-1])
        for i in range(len(self.pages)):
            self.pages.pop().deleteLater()
        self.frame.deleteLater()
        self.jumped_from = None
        self.addRecentFiles()

    def loadPDFfile(self, filename):
        """ Loads pdf document in all threads """
        filename = os.path.expanduser(unicode(filename))
        self.doc = Poppler.Document.load(filename)
        if not self.doc : return
        password = ''
        if self.doc.isLocked() :
            password = QInputDialog.getText(self, 'This PDF is locked', 'Enter Password :', 2)[0].toUtf8()
            if password == '' : sys.exit(1)
            self.doc.unlock(password, password)
        if not self.first_document:
            self.removeOldDoc()
        self.filename = filename
        self.total_pages = self.doc.numPages()
        self.rendered_pages = []
        self.first_document = False
        self.getOutlines(self.doc)
        # Load Document in other threads
        self.loadFileRequested.emit(self.filename, password)
        if collapseUser(self.filename) in self.history_filenames:
            self.current_page = int(self.history_page_no[self.history_filenames.index(collapseUser(self.filename))])
        self.current_page = min(self.current_page, self.total_pages-1)
        self.scroll_render_lock = False
        # Add widgets


        self.frame = QFrame(self.scrollAreaWidgetContents)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        #
        self.scrollArea2 = QScrollArea()
        self.scrollArea2.setAlignment(QtCore.Qt.AlignRight)

        self.verticalLayout = QVBoxLayout(self.frame)
        self.horizontalLayout_2.addWidget(self.frame)

        self.scrollArea.verticalScrollBar().setValue(0)
        self.scrollArea.setAlignment(QtCore.Qt.AlignLeft)

        #
        #self.verticalLayout.addWidget(self.searchText, 1, QtCore.Qt.AlignRight)

        # Render 4 pages, (Preload 3 pages)
        self.max_preload = 4 if (self.total_pages > 4) else self.total_pages
        # Add pages
        for i in range(self.total_pages):
            page = PageWidget(self.frame)
            self.verticalLayout.addWidget(page, 0, QtCore.Qt.AlignLeft)
            self.pages.append(page)
        self.resizePages()
        self.pageNoLabel.setText('<b>%i/%i</b>' % (self.current_page+1, self.total_pages) )
        self.gotoPageValidator.setTop(self.total_pages)
        self.setWindowTitle(os.path.basename(self.filename)+ " - Gospel PDF " + __version__)
        if self.current_page != 0 : QtCore.QTimer.singleShot(500, self.jumpToCurrentPage)

    def setRenderedImage(self, page_no, image):
        """ takes a QImage and sets pixmap of the specified page
            when number of rendered pages exceeds a certain number, old page image is
            deleted to save memory """
        self.pages[page_no].setPageData(page_no, QPixmap.fromImage(image), self.doc.page(page_no))
        # Request to render next page
        if self.current_page < page_no < (self.current_page + self.max_preload - 2):
            if (page_no+2 not in self.rendered_pages) and (page_no+2 < self.total_pages):
              self.rendered_pages.append(page_no+2)
              self.renderRequested.emit(page_no+2, self.pages[page_no+2].dpi)
              self.pages[page_no+2].jumpToRequested.connect(self.jumpToPage)
        # Replace old rendered pages with blank image
        if len(self.rendered_pages)>10:
            self.pages[self.rendered_pages[0]].clear()
            self.pages[self.rendered_pages[0]].jumpToRequested.disconnect(self.jumpToPage)
            self.rendered_pages.pop(0)
        if DEBUG : print(page_no), self.rendered_pages

    def renderCurrentPage(self):
        """ Requests to render current page. if it is already rendered, then request
            to render next unrendered page """
        requested = 0
        for page_no in range(self.current_page, self.current_page+self.max_preload):
            if (page_no not in self.rendered_pages) and (page_no < self.total_pages):
                self.rendered_pages.append(page_no)
                self.renderRequested.emit(page_no, self.pages[page_no].dpi)
                self.pages[page_no].jumpToRequested.connect(self.jumpToPage)
                requested += 1
                if DEBUG : print(page_no)
                if requested == 2: return

    def onMouseScroll(self, pos):
        """ Gets the current page number on scrolling, then requests to render"""
        index = self.verticalLayout.indexOf(self.frame.childAt(self.frame.width()/2, pos))
        if index == -1: return
        self.pageNoLabel.setText('<b>%i/%i</b>' % (index+1, self.total_pages) )
        if self.scrollArea.verticalScrollBar().isSliderDown() or self.scroll_render_lock : return
        self.current_page = index
        self.renderCurrentPage()

    def onSliderRelease(self):
        self.onMouseScroll(self.scrollArea.verticalScrollBar().value())

    def opentextFile(self):
        self.dialog = Second(self)
        self.dialog.show()



    def openFile(self):
        #print self.scrollArea.widget()

        filename = QFileDialog.getOpenFileName(self,
                                      "Select Document to Open", "",
                                      "All Files (*)" )

        print QtCore.QFileInfo(filename).suffix()
        if not filename.isEmpty():
            if QtCore.QFileInfo(filename).suffix() == "pdf":
                self.loadPDFfile(filename)

            elif QtCore.QFileInfo(filename).suffix() in ["docx","odt"]:
                print filename

                os.system('doc2pdf '+ str(filename))

                filename = os.path.splitext(str(filename))[0]+'.pdf'
                print filename
                self.loadPDFfile(filename)

            else:
                file = open(filename, "r")
                self.text = file.read()

                self.textEdit = QTextEdit()
                self.textEdit.setText(self.text)

                fname = "temp.pdf"
                if fname:
                    printer = QPrinter(QPrinter.HighResolution)
                    printer.setPageSize(QPrinter.A4)
                    printer.setColorMode(QPrinter.Color)
                    printer.setOutputFormat(QPrinter.PdfFormat)
                    printer.setOutputFileName(fname)

                    self.textEdit.document().print_(printer)

                    filename = "temp.pdf"
                    self.loadPDFfile(filename)


    def exportToPS(self):
        width = self.doc.page(self.current_page).pageSizeF().width()
        height = self.doc.page(self.current_page).pageSizeF().height()
        filename = QFileDialog.getSaveFileName(self, "Select File to Save",
                                       os.path.splitext(self.filename)[0]+'.ps',
                                      "Adobe Postscript Format (*.ps)" )
        if filename == '' : return
        conv = self.doc.psConverter()
        conv.setPaperWidth(width)
        conv.setPaperHeight(height)
        conv.setOutputFileName(filename)
        conv.setPageList([i+1 for i in range(self.total_pages)])
        ok = conv.convert()
        if ok:
            QMessageBox.information(self, "Successful !","File has been successfully exported")
        else:
            QMessageBox.warning(self, "Failed !","Failed to export to Postscript")

    def docInfo(self):
        info_keys = list(self.doc.infoKeys())
        values = [unicode(self.doc.info(key)) for key in info_keys]
        page_size = self.doc.page(self.current_page).pageSizeF()
        page_size = "%s x %s pts"%(page_size.width(), page_size.height())
        info_keys += ['Embedded FIles', 'Page Size']
        values += [str(self.doc.hasEmbeddedFiles()), page_size]
        dialog = DocInfoDialog(self)
        dialog.setInfo(info_keys, values)
        dialog.exec_()

    def jumpToCurrentPage(self):
        scrolbar_pos = self.pages[self.current_page].pos().y()
        self.scrollArea.verticalScrollBar().setValue(scrolbar_pos)

    def jumpToPage(self, page_no):
        """ gets the current page no from Main.current_page variable, then scrolls to that position """
        self.jumped_from = self.current_page
        self.current_page = page_no
        self.jumpToCurrentPage()

    def undoJump(self):
        if self.jumped_from == None: return
        self.jumpToPage(self.jumped_from)

    def goNextPage(self):
        if self.current_page == self.total_pages-1 : return
        self.current_page += 1
        self.jumpToCurrentPage()

    def goPrevPage(self):
        if self.current_page == 0 : return
        self.current_page -= 1
        self.jumpToCurrentPage()

    def goFirstPage(self):
        self.current_page = 0
        self.jumpToCurrentPage()

    def goLastPage(self):
        self.current_page = self.total_pages-1
        self.jumpToCurrentPage()

    def gotoPage(self):
        text = self.gotoPageEdit.text()
        if text.isEmpty() : return
        self.jumpToPage(int(text)-1)
        self.gotoPageEdit.clear()
        self.gotoPageEdit.clearFocus()

######################  Zoom and Size Management  ##########################

    def availableWidth(self):
        """ Returns available width for rendering a page """
        dock_width = 0 if self.dockWidget.isHidden() else self.dockWidget.width()
        return self.width() - dock_width - 50

    def resizePages(self):
        '''Resize all pages according to zoom level '''
        page_dpi = self.zoom_levels[self.zoomLevelCombo.currentIndex()]*SCREEN_DPI/100
        fixed_width = self.availableWidth()
        for i in range(self.total_pages):
            pg_width = self.doc.page(i).pageSizeF().width() # width in points
            pg_height = self.doc.page(i).pageSizeF().height()
            if self.zoomLevelCombo.currentIndex() == 0: # if fixed width
                dpi = 72.0*fixed_width/pg_width
            else: dpi = page_dpi
            self.pages[i].dpi = dpi
            self.pages[i].setFixedSize(pg_width*dpi/72.0, pg_height*dpi/72.0)
        for page_no in self.rendered_pages:
            self.pages[page_no].clear()
        self.rendered_pages = []
        self.renderCurrentPage()

    def setZoom(self, index):
        """ Gets called when zoom level is changed"""
        self.scroll_render_lock = True # rendering on scroll is locked as set scroll position
        self.resizePages()
        QtCore.QTimer.singleShot(300, self.afterZoom)

    def zoomIn(self):
        index = self.zoomLevelCombo.currentIndex()
        if index == len(self.zoom_levels) - 1 : return
        if index == 0 : index = 3
        self.zoomLevelCombo.setCurrentIndex(index+1)
        self.setZoom(index+1)

    def zoomOut(self):
        index = self.zoomLevelCombo.currentIndex()
        if index == 1 : return
        if index == 0: index = 4
        self.zoomLevelCombo.setCurrentIndex(index-1)
        self.setZoom(index-1)

    def afterZoom(self):
        scrolbar_pos = self.pages[self.current_page].pos().y()
        self.scrollArea.verticalScrollBar().setValue(scrolbar_pos)
        self.scroll_render_lock = False
#########            Search Text            #########
    def findNext(self):
        text = self.findTextEdit.text()
        #text = self.searchText.text()
        area = self.search_area.adjusted(self.search_area.width(), 1, self.search_area.width(), 1)
        self.findTextRequested.emit(text, self.search_page_no, area, False)
        if self.search_text == text: return
        self.search_text = text
        self.search_area = QtCore.QRectF()
        self.search_page_no = self.current_page

    def findBack(self):
        text = self.findTextEdit.text()
        area = self.search_area.adjusted(-self.search_area.width(), -1, -self.search_area.width(), -1)
        self.findTextRequested.emit(text, self.search_page_no, area, True)
        if self.search_text == text: return
        self.search_text = text
        self.search_area = QtCore.QRectF()
        self.search_page_no = self.current_page

    def onTextFound(self, page_no, area):
        zoom = self.pages[page_no].dpi/72.0
        self.pages[page_no].highlight_area = QtCore.QRectF(area.left()*zoom, area.top()*zoom,
                                                           area.width()*zoom, area.height()*zoom)
        # Alternate method of above two lines
        #matrix = QMatrix(self.pages[page_no].dpi/72.0, 0,0, self.pages[page_no].dpi/72.0,0,0)
        #self.pages[page_no].highlight_area = matrix.mapRect(area).toRect()
        if self.pages[page_no].pixmap():
            self.pages[page_no].updateImage()
        else:
            self.rendered_pages.append(page_no)
            self.renderRequested.emit(page_no, self.pages[page_no].dpi)
        if page_no != self.search_page_no :
            self.pages[self.search_page_no].highlight_area = None
            self.pages[self.search_page_no].updateImage()
            self.jumpToPage(page_no)
        self.search_area = area
        self.search_page_no = page_no

    def toggleFindMode(self, enable):
        if enable:
          self.findTextEdit.setFocus()
          self.search_text = ''
          self.search_area = QtCore.QRectF()
          self.search_page_no = self.current_page
        else:
          self.pages[self.search_page_no].highlight_area = None
          self.pages[self.search_page_no].updateImage()
          self.search_text = ''
          self.search_area = QtCore.QRectF()
          self.findTextEdit.setText('')

#########      Cpoy Text to Clip Board      #########
    def toggleCopyText(self, checked):
        if checked:
            self.copy_text_pages = [self.current_page]
            if self.current_page+1 < self.total_pages: # add next page when current page is not last page
                self.copy_text_pages.append(self.current_page+1)
            for page_no in self.copy_text_pages:
                self.pages[page_no].copy_text_mode = True
                self.pages[page_no].copyTextRequested.connect(self.copyText)
        else:
            self.disableCopyText()

    def disableCopyText(self):
        for page_no in self.copy_text_pages:
            self.pages[page_no].copy_text_mode = False
            self.pages[page_no].copyTextRequested.disconnect(self.copyText)
        self.copy_text_pages = []
        self.copyTextAction.setChecked(False)

    def copyText(self, top_left, bottom_right):
        # Get page number and page zoom level
        page_no = self.pages.index(self.sender())
        zoom = float(self.pages[page_no].height())/float(self.doc.page(page_no).pageSize().height())
        # Copy text to clipboard
        text = self.doc.page(page_no).text(QtCore.QRectF(top_left/zoom, bottom_right/zoom))
        QApplication.clipboard().setText(text)
        self.disableCopyText()
#########      Cpoy Text to Clip Board      ##### ... end

    def getOutlines(self, doc):
        toc = doc.toc()
        if not toc:
            self.dockWidget.hide()
            return
        self.dockWidget.show()
        outline_model = QStandardItemModel(self)
        parent_item = outline_model.invisibleRootItem()
        node = toc.firstChild()
        loadOutline(doc, node, parent_item)
        self.treeView.setModel(outline_model)
        if parent_item.rowCount() < 3:
            self.treeView.expandToDepth(0)
        self.treeView.setHeaderHidden(True)
        self.treeView.header().setResizeMode(0, 1)
        self.treeView.header().setResizeMode(1, 3)
        self.treeView.header().setStretchLastSection(False)

    def onOutlineClick(self, m_index):
        page = self.treeView.model().data(m_index, QtCore.Qt.UserRole+1).toString()
        if page == "": return
        self.jumpToPage(int(page)-1)

    def resizeEvent(self, ev):
        QMainWindow.resizeEvent(self, ev)
        if self.filename == '' : return
        if self.zoomLevelCombo.currentIndex() == 0:
            self.resize_page_timer.start(200)

    def onWindowResize(self):
        for i in range(self.total_pages):
            self.pages[i].annots_listed = False # Clears prev link annotation positions
        self.resizePages()
        wait(300)
        self.jumpToCurrentPage()
        if not self.isMaximized():
            self.settings.setValue("WindowWidth", self.width())
            self.settings.setValue("WindowHeight", self.height())

    def saveFileData(self):
        if self.filename != '':
            filename = collapseUser(self.filename)
            if filename in self.history_filenames:
                index = self.history_filenames.index(filename)
                self.history_page_no[index] = self.current_page
            else:
                self.history_filenames.insert(0, filename)
                self.history_page_no.insert(0, self.current_page)
            if filename in self.recent_files:
                self.recent_files.remove(filename)
            self.recent_files.insert(0, filename)

    def closeEvent(self, ev):
        """ Save all settings on window close """
        self.saveFileData()
        self.settings.setValue("OffsetX", self.geometry().x()-self.x())
        self.settings.setValue("OffsetY", self.geometry().y()-self.y())
        self.settings.setValue("ZoomLevel", self.zoomLevelCombo.currentIndex())
        self.settings.setValue("HistoryFileNameList", self.history_filenames[:100])
        self.settings.setValue("HistoryPageNoList", self.history_page_no[:100])
        self.settings.setValue("RecentFiles", self.recent_files[:10])
        return super(Main, self).closeEvent(ev)

    def onAppQuit(self):
        """ Close running threads """
        loop1 = QtCore.QEventLoop()
        loop2 = QtCore.QEventLoop()
        self.thread1.finished.connect(loop1.quit)
        self.thread2.finished.connect(loop2.quit)
        self.thread1.quit()
        loop1.exec_()
        self.thread2.quit()
        loop2.exec_()


def loadOutline(document, node, prnt_item):
    """void loadOutline(Poppler::Document* document, const QDomNode& node, QStandardItem* prnt_item) """
    element = node.toElement()
    item = QStandardItem(element.tagName())

    linkDestination = None
    if element.hasAttribute("Destination"):
        linkDestination = Poppler.LinkDestination(element.attribute("Destination"))
    elif element.hasAttribute("DestinationName"):
        linkDestination = document.linkDestination(element.attribute("DestinationName"))

    if linkDestination:
        page = linkDestination.pageNumber()
        if page < 1 : page = 1
        if page > document.numPages(): page = document.numPages()

        item.setData(page, QtCore.Qt.UserRole + 1)

        pageItem = item.clone()
        pageItem.setText(str(page))
        pageItem.setTextAlignment(QtCore.Qt.AlignRight)

        prnt_item.appendRow([item, pageItem])
    else:
        prnt_item.appendRow(item)

    # Load next sibling
    siblingNode = node.nextSibling()
    if not siblingNode.isNull():
        loadOutline(document, siblingNode, prnt_item)

    # Load its child
    childNode = node.firstChild()
    if not childNode.isNull():
        loadOutline(document, childNode, item)

class PageWidget(QLabel):
    jumpToRequested = QtCore.pyqtSignal(int)
    copyTextRequested = QtCore.pyqtSignal(QtCore.QPoint, QtCore.QPoint)

    def __init__(self, parent=None):
        QLabel.__init__(self, parent)
        self.setMouseTracking(True)
        self.setSizePolicy(0,0)
        self.setFrameShape(QFrame.StyledPanel)
        self.link_areas = []
        self.link_annots = []
        self.annots_listed, self.copy_text_mode, self.click_point, self.highlight_area = False, False, None, None
        self.image = QPixmap()

    def setPageData(self, page_no, pixmap, page):
        self.image = pixmap
        self.updateImage()
        if self.annots_listed : return
        annots = page.annotations()
        for annot in annots:
            if annot.subType() == Poppler.Annotation.ALink:
                x, y = annot.boundary().left()*pixmap.width(), annot.boundary().top()*pixmap.height()
                w, h = annot.boundary().width()*pixmap.width()+1, annot.boundary().height()*pixmap.height()+1
                self.link_areas.append(QtCore.QRectF(x,y, w, h))
                self.link_annots.append(annot)
        self.annots_listed = True

    def clear(self):
        QLabel.clear(self)
        self.image = QPixmap()

    def mouseMoveEvent(self, ev):
        # Draw rectangle when mouse is clicked and dragged in copy text mode.
        if self.copy_text_mode:
            if self.click_point:
                pm = self.pm.copy()
                painter = QPainter()
                painter.begin(pm)
                painter.setBrush(QColor(000,000,255,80))
                painter.drawRect(QtCore.QRect(self.click_point, ev.pos()))
                painter.end()
                self.setPixmap(pm)
            return

        # Change cursor if cursor is over link annotation
        self.unsetCursor()
        for area in self.link_areas:
            if area.contains(ev.pos()):
                self.setCursor(QtCore.Qt.PointingHandCursor)
                break

    def mousePressEvent(self, ev):
        #if self.cursor() != QtCore.Qt.PointingHandCursor: return
        # In text copy mode
        if self.copy_text_mode:
            self.click_point = ev.pos()
            self.pm = self.pixmap().copy()
            return
        # In normal mode
        for i, area in enumerate(self.link_areas):
            if area.contains(ev.pos()):
              # For jump to page link
              if self.link_annots[i].linkDestination().linkType() == Poppler.Link.Goto:
                p = self.link_annots[i].linkDestination().destination().pageNumber()
                self.jumpToRequested.emit(p-1)
              # For URL link
              elif self.link_annots[i].linkDestination().linkType() == Poppler.Link.Browse:
                p = self.link_annots[i].linkDestination().url()
                if p.startsWith("http"):
                  confirm = QMessageBox.question(self, "Open Url in Browser",
                            "Do you want to open browser to open...\n%s"%p, QMessageBox.Yes|QMessageBox.Cancel)
                  if confirm == 0x00004000:
                    Popen(["x-www-browser", p])
              return

    def mouseReleaseEvent(self, ev):
        if self.copy_text_mode:
            self.copyTextRequested.emit(self.click_point, ev.pos())
            self.click_point = None
            self.setPixmap(self.pm)

    def updateImage(self):
        #if self.image.isNull() : return
        if self.highlight_area:
            img = self.image.copy()
            painter = QPainter(img)
            painter.fillRect(self.highlight_area, QColor(0,255,0, 127))
            painter.end()
            self.setPixmap(img)
        else:
            self.setPixmap(self.image)

class DocInfoDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.resize(560, 320)
        self.tableWidget = QTableWidget(0, 2, self)
        vLayout = QVBoxLayout(self)
        vLayout.addWidget(self.tableWidget)
        self.tableWidget.setAlternatingRowColors(True)
        closeBtn = QPushButton(QIcon(':/quit.png'), "Close", self)
        closeBtn.setMaximumWidth(120)
        vLayout.addWidget(closeBtn, 0, QtCore.Qt.AlignRight)
        closeBtn.clicked.connect(self.accept)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.tableWidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setVisible(False)

    def setInfo(self, info_keys, values):
        for i in range(len(info_keys)):
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(i,0, QTableWidgetItem(info_keys[i]))
            self.tableWidget.setItem(i,1, QTableWidgetItem(values[i]))


class Second(Main):
    def __init__(self, parent=None):
        super(Second, self).__init__(parent)


        #self.openBtn = QPushButton("Open text file")
        #self.openBtn.clicked.connect(self.on_pushButton_clicked)

        self.textEdit = QTextEdit()

        self.table = QTableWidget()
        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels(QtCore.QString("Page;Document Title;Text").split(";"))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setColumnWidth(0,50)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.table.setRowCount(18)

        self.table.setMinimumHeight(600)

        gbSearch = QGroupBox('Search..')
        self.pageNavigratorSearch = QHBoxLayout() #create Horizontal Box layout

        self.searchText =  QLineEdit("Rear Admiral")

        self.searchBtn = QPushButton('Search') #search btn


        self.date1 = QDateEdit()
        self.date1.setDisplayFormat('dd/MM/yyyy')
        self.date1.setCalendarPopup(True)
        self.date1.setDate(QtCore.QDate.currentDate())


        self.date2 = QDateEdit()
        self.date2.setDisplayFormat('dd/MM/yyyy')
        self.date2.setCalendarPopup(True)
        self.date2.setDate(QtCore.QDate.currentDate())

        self.pageNavigratorSearch.addWidget(self.date1) #add cal cal2 and button to horizontal layout
        self.pageNavigratorSearch.addWidget(self.date2)
        self.pageNavigratorSearch.addWidget(self.searchBtn)

        gbSearch.setLayout(self.pageNavigratorSearch)

        self.configureLayout = QGridLayout()      #------Another grid layout----------
        self.configureLayout.addWidget(self.searchText , 0, 0) #----adding line edit to layout
        self.configureLayout.addWidget(gbSearch , 1, 0) #-------adding gbsearch groupbox to layout
        #self.configureLayout.addWidget(self.searchBtn,2,0)
        self.configureLayout.addWidget(self.table , 2, 0) #--------adding table to layout-----
        self.configureLayout.setHorizontalSpacing(2)

        self.configureWidget = QWidget()
        self.configureWidget.setMaximumWidth(550)
        self.configureWidget.setLayout(self.configureLayout)

        self.commentsLayout = QGridLayout()  # --------------Another Grid layout--------

        self.commentsTable = QTableWidget() #---------craeting comment table------
        self.commentsTable.setColumnCount(2)
        self.commentsTable.setRowCount(4)
        self.commentsTable.setHorizontalHeaderLabels(QtCore.QString(";User").split(";"))
        self.commentsTable.horizontalHeader().setStretchLastSection(True)
        self.commentsTable.verticalHeader().hide()
        self.commentsTable.setColumnWidth(0,50)
        self.commentsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.commentsTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.commentsViewTable = QTableWidget() #------------creating Another comment table----
        self.commentsViewTable.setColumnCount(2)
        self.commentsViewTable.setRowCount(4)

        self.commentsViewTable.setHorizontalHeaderLabels(QtCore.QString(";Comment").split(";"))
        self.commentsViewTable.horizontalHeader().setStretchLastSection(True)
        self.commentsViewTable.verticalHeader().hide()
        self.commentsViewTable.setColumnWidth(0,50)
        self.commentsViewTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.commentsViewTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.commentsViewTable.setMinimumHeight(600)
        self.commentsLayout.addWidget(self.commentsTable ,0,0,QtCore.Qt.AlignTop ) #----------adding table to the layout
        self.commentsLayout.addWidget(self.commentsViewTable ,1,0)
        self.commentsLayout.setRowStretch(0,3)
        # self.commentsTable.setStretch(0, 1)
        self.commentsLayout.setHorizontalSpacing(2)

        self.commentsWidget = QWidget()
        self.commentsWidget.setMaximumWidth(300)
        self.commentsWidget.setLayout(self.commentsLayout)


        self.mainLayout = QGridLayout() # --------Main Layout-----------------------
        #self.mainLayout.addWidget(self.openBtn,0,0)
        self.mainLayout.addWidget(self.textEdit, 1,0)  #-------------adding grids to ths main layout----------
        self.mainLayout.addWidget(self.commentsWidget , 1,2)
        self.mainLayout.addWidget(self.configureWidget , 1,3)

        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.mainLayout)

        self.showMaximized()

        # fname = QFileDialog.getOpenFileName(self, 'Open file',
        #         '/home')

        f = open(self.filename, 'r')

        with f:
            data = f.read()
            self.textEdit.setText(data)


    # def on_pushButton_clicked(self):
    #
    #     fname = QFileDialog.getOpenFileName(self, 'Open file',
    #             '/home')
    #
    #     f = open(fname, 'r')
    #
    #     with f:
    #         data = f.read()
    #         self.textEdit.setText(data)










def wait(millisec):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(millisec, loop.quit)
    loop.exec_()

def collapseUser(path):
    ''' converts /home/user/file.ext to ~/file.ext '''
    path = unicode(path)
    if path.startswith(HOMEDIR):
        return path.replace(HOMEDIR, '~', 1)
    return path

def elideMiddle(text, length):
    if len(text) <= length: return text
    return text[:length//2] + '...' + text[len(text)-length+length//2:]

def main():
    app = QApplication(sys.argv)
    win = Main()
    if len(sys.argv)>1 and os.path.exists(os.path.abspath(sys.argv[-1])):
        win.loadPDFfile(QtCore.QString.fromUtf8(os.path.abspath(sys.argv[-1])))
    app.aboutToQuit.connect(win.onAppQuit)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
