import platform
import sys
import os
from PyQt6.QtCore import * 
from PyQt6.QtGui import * 
from PyQt6.QtWidgets import *
import sourceHandling as srcHnd
# from PyQt6.QtCore import Qt
import base64

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

icon_path = resource_path("icons/check_blue_4.png")

TEXT_COLOR = "white"
FADED_TEXT_COLOR = "#b0b0b0"
BUTTON_COLOR = "#535454"
HEADER_BG_COLOR = "#535454"
TEXT_FIELD_COLOR = "#232424"
BUTTON_STYLESHEET = f"""
    QPushButton {{             
        background-color: {BUTTON_COLOR};
        color: {TEXT_COLOR};
        height: 20px;
    }}

    QPushButton:disabled {{             
        color: {FADED_TEXT_COLOR};
    }}

    QPushButton:pressed {{
       padding-left: 7px;  /* simulate "pressed-in" effect */
       padding-top: 7px;
    }}
"""


DROPDOWN_STYLESHEET = f"""
    QComboBox {{             
        background-color: {HEADER_BG_COLOR};
        color: {TEXT_COLOR};
        padding-left: 5px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {HEADER_BG_COLOR};  /* or another color if you want */
        color: {TEXT_COLOR};
        selection-background-color: {TEXT_FIELD_COLOR};
        selection-color: {TEXT_COLOR};  /* Optional: for selected item text */
        border: none;
    }}

    QComboBox::item:selected{{             
        background-color: {TEXT_FIELD_COLOR};
    }}

    QComboBox:disabled{{             
        background-color: {HEADER_BG_COLOR};
        color: {FADED_TEXT_COLOR};
    }}
"""
CHECKBOX_STYLESHEET = f"""
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
    }}

    QCheckBox::indicator:unchecked {{
        background-color : {TEXT_FIELD_COLOR}
    }}

    QCheckBox::indicator:checked {{
        image: url({icon_path})
    }}

    QCheckBox {{
        color: {TEXT_COLOR}
        spacing: 10px; /* space between checkbox and text */
    }}
"""
# image: url("data:image/png;base64,{checkbox_icon_b64}");
# border-image: url("data:image/png;base64,{checkbox_icon_b64}") 0 0 0 0 stretch stretch;

class NoCheckmarkDelegate(QStyledItemDelegate):
    def paint(self, painter, option: QStyleOptionViewItem, index):
        # Disable the checkmark indicator (this preserves stylesheets)
        option.features &= ~QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        super().paint(painter, option, index)

class ListItem(QLabel):
    clicked = pyqtSignal()

    def __init__(self, title: str, parentWindow, parent=None):
        super().__init__(parent)
        self.parentWindow = parentWindow
        self.position = 0
        self.filePath = title
        self.fileSelected = False
        self.setText(self.filePath)
        self.setSelected()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
    def on_click_label(self):
        self.setSelected()
        self.parentWindow.unselectUI(self.position)

    def setSelected(self):
        self.selected = True
        self.color = "#4b9bbf"
        self.setStyleSheet(f"background-color:{self.color} ; color: {TEXT_COLOR}; font-size: 12px")

    def setUnselected(self):
        self.selected = False
        self.color = "#232424"
        self.setStyleSheet(f"background-color:{self.color} ; color: {TEXT_COLOR}; font-size: 12px")
        
    def mousePressEvent(self, event):
        """
        Overrides the mousePressEvent to emit the custom 'clicked' signal.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event) #

class CustomComboBox(QComboBox):
    def __init__(self, itemList):
        super().__init__()

        model = QStandardItemModel()
        for item_text in itemList:
            item = QStandardItem(item_text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)  # Disable checkable
            model.appendRow(item)

        self.setItemDelegate(NoCheckmarkDelegate(self))

        self.setModel(model)

        self.setStyleSheet(DROPDOWN_STYLESHEET)

    def showPopup(self):
        super().showPopup()
        # align popup to top-left of combobox
        popup_widget = self.view().parentWidget()

        top_left_global = self.mapToGlobal(QPoint(0, 0))
        popup_widget.move(top_left_global)


class CustomIndicatorCheckBox(QCheckBox):
    def __init__(self, text, box_color="#3A3A3A", check_bg="#2D7FFF"):
        super().__init__(text)
        self.box_color = QColor(box_color)
        self.check_bg = QColor(check_bg)

        icon_path = resource_path("icons/check_blue_4.png")
        with open(icon_path, "rb") as f:
            checkbox_icon_b64 = base64.b64encode(f.read()).decode("ascii")

        self.check_pixmap = QPixmap()
        self.check_pixmap.loadFromData(base64.b64decode(checkbox_icon_b64))

        # Optional stylesheet for spacing + text color
        self.setStyleSheet("QCheckBox { spacing: 8px; color: white; }")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Size and position for the checkbox square
        indicator_size = 16
        rect = QRect(0, (self.height() - indicator_size) // 2, indicator_size, indicator_size)

        # Draw box background
        if self.isChecked():
            painter.setBrush(self.check_bg)
        else:
            painter.setBrush(self.box_color)

        painter.setPen(QColor("#555"))
        painter.drawRoundedRect(rect, 3, 3)

        # Draw the checkmark PNG scaled to fit inside the box
        if self.isChecked() and not self.check_pixmap.isNull():
            scaled = self.check_pixmap.scaled(
                indicator_size - 4,  # leave a 2px margin
                indicator_size - 4,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Center it inside the box
            x = rect.x() + (rect.width() - scaled.width()) // 2
            y = rect.y() + (rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        # Draw text next to checkbox
        text_rect = QRect(rect.right() + 8, 0, self.width() - rect.width() - 8, self.height())
        painter.setPen(QColor("white"))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, self.text())

        painter.end()


class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.toggle_button = QToolButton(text=title, checkable=True, checked=True)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                
                background-color: #535454;
                color: white;
                border: none;
                text-align: left;
                padding: 2px;
            }
        """)
        font = self.toggle_button.font()
        font.setPointSize(14)  # or whatever size you want
        self.toggle_button.setFont(font)

        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_button.clicked.connect(self.toggle)

        self.content_area = QScrollArea(maximumHeight=0, minimumHeight=0)
        self.content_area.setWidgetResizable(True)
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.content_area.setFrameShape(QFrame.Shape.NoFrame)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

        self.toggle_animation_duration = 150
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def toggle(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        if checked:
            content_height = self.content_area.widget().sizeHint().height()
            self.content_area.setMaximumHeight(content_height)
            self.content_area.setVisible(True)
        else:
            self.content_area.setMaximumHeight(0)
            self.content_area.setVisible(False)
    
    def auto_collapse(self):
        if self.toggle_button.isChecked():
            self.toggle_button.setChecked(False)
            self.toggle()

    def setContentLayout(self, content_layout):
        # Wrapper widget for the layout
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.content_area.setWidget(content_widget)
        # Expand content area immediately
        content_height = content_widget.sizeHint().height()
        self.content_area.setMaximumHeight(content_height)
        
class ConverMovieGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.__createWindow()
        self.__createGUIElements()

    def __createWindow(self):
        self.setWindowTitle("Convert Movie")  # Set the window title
        self.setGeometry(100, 100, 600, 200)  # Set position and size (x, y, width, height)
        self.resize(600,200) 


        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.setStyleSheet("background-color: #333333;")

    def __createGUIElements(self):
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)

        ## FFMPEG SECTION
        self.ffmpeg_section = CollapsibleSection(" FFMPEG")
        self.ffmpeg_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Content for the collapsible section
        self.ffmpeg_layout = QVBoxLayout()
        self.addFfmpegWidgets(self.ffmpeg_layout)
        self.ffmpeg_layout.addStretch()

        self.ffmpeg_section.setContentLayout(self.ffmpeg_layout)
        self.mainLayout.addWidget(self.ffmpeg_section)

        # Create a horizontal separator
        self.separator1 = QFrame()
        self.separator1.setFrameShape(QFrame.Shape.HLine)  # Horizontal line
        self.separator1.setFrameShadow(QFrame.Shadow.Sunken) # Optional shadow effect
        self.mainLayout.addWidget(self.separator1)

        ## INPUT SOURCES SECTION

        self.input_section = CollapsibleSection(" Input Options")
        self.input_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_layout = QVBoxLayout()
        self.addInputWidgets(self.input_layout)
        self.input_layout.addStretch()

        self.input_section.setContentLayout(self.input_layout)
        self.mainLayout.addWidget(self.input_section)

        # Create a horizontal separator
        self.separator2 = QFrame()
        self.separator2.setFrameShape(QFrame.Shape.HLine)  # Horizontal line
        self.separator2.setFrameShadow(QFrame.Shadow.Sunken) # Optional shadow effect
        self.mainLayout.addWidget(self.separator2)

        ## OUTPUT SECTION

        self.output_section = CollapsibleSection(" Output Options")
        self.output_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Content for the collapsible section
        self.output_layout = QVBoxLayout()
        self.addOutputWidgets(self.output_layout)
        self.output_layout.addStretch()

        self.output_section.setContentLayout(self.output_layout)
        self.mainLayout.addWidget(self.output_section)

        # Create a horizontal separator
        self.separator3 = QFrame()
        self.separator3.setFrameShape(QFrame.Shape.HLine)  # Horizontal line
        self.separator3.setFrameShadow(QFrame.Shadow.Sunken) # Optional shadow effect
        self.mainLayout.addWidget(self.separator3)

        ## LOG Section
        self.outputLogText = QTextEdit()
        self.outputLogText.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR}; color: {FADED_TEXT_COLOR}")
        self.outputLogText.setPlaceholderText("Output Logs...")
        self.mainLayout.addWidget(self.outputLogText)

        self.centralWidget.setLayout(self.mainLayout)
        


    def addFfmpegWidgets(self, sectionLayout):

        self.osSection = QHBoxLayout()
        self.OSlabel = QLabel("OS:")
        self.OSlabel.setStyleSheet(f"padding-left: 1px; color: {TEXT_COLOR};")
        self.OSlabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.osSection.addWidget(self.OSlabel)

        self.PCradioButton = QRadioButton("PC")
        self.PCradioButton.setStyleSheet(f"color: {TEXT_COLOR};")
        
        self.PCradioButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.osSection.addWidget(self.PCradioButton)

        self.MACradioButton = QRadioButton("MAC")
        self.MACradioButton.setStyleSheet(f"color: {TEXT_COLOR};")
        self.MACradioButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.osSection.addWidget(self.MACradioButton)

        if srcHnd.getOS():
            self.PCradioButton.setChecked(True)
            self.MACradioButton.setEnabled(False)
        else:
            self.MACradioButton.setChecked(True)
            self.PCradioButton.setEnabled(False)
        sectionLayout.addLayout(self.osSection)

        self.ffmpegBrowseSection = QHBoxLayout()

        self.ffmpegLoc = QLineEdit()
        self.ffmpegLoc.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR};")
        self.ffmpegLoc.setTextMargins(5, 0, 0, 0)
        self.ffmpegLoc.setReadOnly(True)
        ffmpegPath, isfound = srcHnd.verifyFFMPEG()
        self.ffmpegLoc.setText(ffmpegPath)
        if isfound:
            self.ffmpegLoc.setStyleSheet(f"background-color: #548050; color: {TEXT_COLOR};")
            self.ffmpeg_section.auto_collapse()
        else:
            self.ffmpegLoc.setStyleSheet(f"background-color: #b55151; color: {TEXT_COLOR};")
        self.ffmpegLoc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ffmpegBrowseSection.addWidget(self.ffmpegLoc)

        self.browseBtn = QPushButton(text="Browse", parent=self.ffmpegLoc)
        self.browseBtn.setStyleSheet(f"background-color: {BUTTON_COLOR}; color: {TEXT_COLOR};")
        self.ffmpegBrowseSection.addWidget(self.browseBtn, alignment = Qt.AlignmentFlag.AlignRight)
        self.browseBtn.clicked.connect(self.browseBtnClicked)

        sectionLayout.addLayout(self.ffmpegBrowseSection)
      
    def browseBtnClicked(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select FFMPEG File", "", "All Files (*)")
        ffmpegPath, isfound = srcHnd.verifyFFMPEG(fileName)
        self.ffmpegLoc.setText(ffmpegPath)
        if isfound:
            self.ffmpegLoc.setStyleSheet(f"background-color: #548050; color: {TEXT_COLOR};")
            self.ffmpeg_section.auto_collapse()
        else:
            self.ffmpegLoc.setStyleSheet(f"background-color: #b55151; color: {TEXT_COLOR};")
        # self.ffmpegLoc.setText(srcHnd.fUt.check_ffmpeg(fileName))

    def addInputWidgets(self, sectionLayout):

        self.sourceListArea = QScrollArea(maximumHeight=100, minimumHeight=100)
        # self.content_area.setWidgetResizable(True)

        self.sourceListWidget= QWidget()
        self.sourceListWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.sourceListLayout = QVBoxLayout(self.sourceListWidget)

        self.sourceList = []
        self.source1Label = ListItem("Source 1", parentWindow = self)
        self.currentlySelectedSrcInd = self.source1Label.position
        self.sourceList.append(self.source1Label)
        self.source1Label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.sourceListLayout.addWidget(self.source1Label)
        self.source1Label.clicked.connect(self.source1Label.on_click_label)

        self.sourceListArea.setWidget(self.sourceListWidget)

        self.sourceListArea.setWidgetResizable(True)

        self.sourceListArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.sourceListArea.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR};")
        self.sourceListArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.sourceListArea.setFrameShape(QFrame.Shape.Box)



        self.sourceListLayout.addStretch()

        sectionLayout.addWidget(self.sourceListArea)
        


        self.sourceOptionsLabel = QLabel("Source 1")
        self.sourceOptionsLabel.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; color: {TEXT_COLOR}; padding: 4px")
        self.sourceOptionsLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sectionLayout.addWidget(self.sourceOptionsLabel)

        self.sourceSelLayout = QHBoxLayout()

        self.inputLabel = QLabel("Input File")
        self.inputLabel.setStyleSheet(f"color: {TEXT_COLOR};")
        self.sourceSelLayout.addWidget(self.inputLabel)
        self.sourceLoc = QLineEdit()
        self.sourceLoc.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR}; color: {TEXT_COLOR};")
        self.sourceLoc.setTextMargins(5, 0, 0, 0)
        self.sourceLoc.setReadOnly(True)
        self.sourceLoc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.sourceSelLayout.addWidget(self.sourceLoc)

        self.inputBrowseBtn = QPushButton(text="Browse", parent=self.sourceLoc)
        self.inputBrowseBtn.setStyleSheet(f"background-color: {BUTTON_COLOR};color: {TEXT_COLOR};")
        self.sourceSelLayout.addWidget(self.inputBrowseBtn, alignment = Qt.AlignmentFlag.AlignRight)
        self.inputBrowseBtn.clicked.connect(self.inputBrowseBtnClicked)

        sectionLayout.addLayout(self.sourceSelLayout)

        self.sourceBtnsLayout = QHBoxLayout()

        self.moveUpBtn = QPushButton(text="Move Up", parent=self.sourceOptionsLabel)
        self.moveUpBtn.setStyleSheet(BUTTON_STYLESHEET)
        self.sourceBtnsLayout.addWidget(self.moveUpBtn)
        self.moveUpBtn.setEnabled(False) 
        self.moveUpBtn.clicked.connect(self.moveUpBtnClicked)

        self.moveDownBtn = QPushButton(text="Move Down", parent=self.sourceOptionsLabel)
        self.moveDownBtn.setStyleSheet(BUTTON_STYLESHEET)
        self.sourceBtnsLayout.addWidget(self.moveDownBtn)
        self.moveDownBtn.setEnabled(False) 
        self.moveDownBtn.clicked.connect(self.moveDownBtnClicked)

        self.deleteBtn = QPushButton(text="Delete", parent=self.sourceOptionsLabel)
        self.deleteBtn.setStyleSheet(BUTTON_STYLESHEET)
        self.sourceBtnsLayout.addWidget(self.deleteBtn)
        self.deleteBtn.setEnabled(False) 
        self.deleteBtn.clicked.connect(self.deleteBtnClicked)

        self.addSrcBtn = QPushButton(text="Add Source", parent=self.sourceOptionsLabel)
        self.addSrcBtn.setStyleSheet(BUTTON_STYLESHEET)
        self.sourceBtnsLayout.addWidget(self.addSrcBtn)
        self.addSrcBtn.clicked.connect(self.addNewSrcUI)

        sectionLayout.addLayout(self.sourceBtnsLayout)

    def inputBrowseBtnClicked(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "Image/Video Files (*.png *.jpg *.jpeg *.mp4 *.avi *.mov)")
        if filePath:
            sourceVerified, pathTodisplay = srcHnd.verifySource(filePath)
            if sourceVerified:
                srcLabel = self.sourceList[self.currentlySelectedSrcInd]

                # srcHnd.addSource(filePath, self.currentlySelectedSrcInd, srcLabel.fileSelected)

                srcLabel.setText(filePath)
                srcLabel.filePath = filePath
                srcLabel.fileSelected = True
                srcLabel.position = self.currentlySelectedSrcInd

                self.sourceLoc.setText(pathTodisplay)

                if self.currentlySelectedSrcInd == 0:
                    self.setOutputDimensions(filePath)
            else:
                self.msg = QMessageBox(self) # Pass self as parent for proper modality
                self.msg.setWindowTitle("Error")
                self.msg.setText("If you're selecting a sequence of images, please select the First image: \"0001\"")
                self.msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                result = self.msg.exec()


    def addNewSrcUI(self, fileName):
        
        self.sourceLoc.setText("")
        numSources = len(self.sourceList)
        self.sourceOptionsLabel.setText(f"Source {numSources+1}")

        self.srcLabel = ListItem(f"Source {numSources+1}", parentWindow = self)
        self.sourceList.append(self.srcLabel)
        self.srcLabel.position = numSources
        self.unselectUI(self.srcLabel.position)
        self.srcLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.sourceListLayout.insertWidget(self.sourceListLayout.count() - 1, self.srcLabel)
        self.srcLabel.clicked.connect(self.srcLabel.on_click_label)

        self.moveUpBtn.setEnabled(True) 
        self.moveDownBtn.setEnabled(True) 
        self.deleteBtn.setEnabled(True)

    def deleteBtnClicked(self):
        sourceLabeltoDelete = self.sourceList.pop(self.currentlySelectedSrcInd) # remove from source label list
        if sourceLabeltoDelete:
            # if srcHnd.deleteFromSources(sourceLabeltoDelete.position):
            sourceLabeltoDelete.deleteLater()
            sourceLabeltoDelete = None
            if self.currentlySelectedSrcInd > 0:
                self.currentlySelectedSrcInd -=1
                prevLabel = self.sourceList[self.currentlySelectedSrcInd]
                prevLabel.setSelected()# select previous one
                if not prevLabel.fileSelected: # update label text number for previous one
                    prevLabel.setText(f"Source {self.currentlySelectedSrcInd+1}")

                # update positions and labels for the remaining ones
                for src in self.sourceList[self.currentlySelectedSrcInd+1:]:
                    if not src.fileSelected:
                        src.position -=1
                        src.setText(f"Source {src.position+1}")
                        
            else:
                # if failed, select the next one
                print("selecting next one")
                nextLabel = self.sourceList[self.currentlySelectedSrcInd]
                nextLabel.setSelected()
                for src in self.sourceList:
                    if not src.fileSelected:
                        src.position -=1 
                        src.setText(f"Source {src.position+1}")
            self.unselectUI(self.currentlySelectedSrcInd)

        
        if len(self.sourceList) <=1:
            self.deleteBtn.setEnabled(False)
            self.moveUpBtn.setEnabled(False)
            self.moveDownBtn.setEnabled(False)

    def moveUpBtnClicked(self):
        if self.currentlySelectedSrcInd > 0:
            # srcHnd.moveInSrc(self.currentlySelectedSrcInd, self.currentlySelectedSrcInd-1 , len(self.sourceList))
            self.sourceList[self.currentlySelectedSrcInd -1].position +=1
            sourceLabeltoMove = self.sourceList.pop(self.currentlySelectedSrcInd)
            self.sourceList.insert(sourceLabeltoMove.position -1, sourceLabeltoMove)
            sourceLabeltoMove.position -=1
            self.currentlySelectedSrcInd -=1

            curr_layoutLabelInd = self.sourceListLayout.indexOf(sourceLabeltoMove)
            if curr_layoutLabelInd > 0:
                print("here")
                item = self.sourceListLayout.takeAt(curr_layoutLabelInd)
                widget = item.widget()
                if widget:
                    self.sourceListLayout.insertWidget(curr_layoutLabelInd - 1, widget)
                    # Optional: Ensure the moved item is visible
                    self.sourceListArea.ensureWidgetVisible(widget)
        
    def moveDownBtnClicked(self):
        if self.currentlySelectedSrcInd < len(self.sourceList) -1:
            # srcHnd.moveInSrc(self.currentlySelectedSrcInd, self.currentlySelectedSrcInd+1, len(self.sourceList) )
            self.sourceList[self.currentlySelectedSrcInd +1].position -=1
            sourceLabeltoMove = self.sourceList.pop(self.currentlySelectedSrcInd)
            print(sourceLabeltoMove.text())
            self.sourceList.insert(sourceLabeltoMove.position +1, sourceLabeltoMove)
            sourceLabeltoMove.position +=1
            self.currentlySelectedSrcInd +=1
            print(self.sourceList[self.currentlySelectedSrcInd].text())

            curr_layoutLabelInd = self.sourceListLayout.indexOf(sourceLabeltoMove)
            count = self.sourceListLayout.count()
            # Adjust count if the layout ends with a stretch or spacer
            while count > 0 and self.sourceListLayout.itemAt(count - 1).spacerItem():
                count -= 1
            if 0 <= curr_layoutLabelInd < count - 1:
                print("here")
                item = self.sourceListLayout.takeAt(curr_layoutLabelInd)
                widget = item.widget()
                if widget:
                    self.sourceListLayout.insertWidget(curr_layoutLabelInd + 1, widget)
                    # Optional: Ensure the moved item is visible
                    self.sourceListArea.ensureWidgetVisible(widget)

    def unselectUI(self, selectedSrcLabelInd):
        if(self.currentlySelectedSrcInd != selectedSrcLabelInd):
            try:
                self.sourceList[self.currentlySelectedSrcInd].setUnselected()
            except IndexError:
                pass
            self.currentlySelectedSrcInd = selectedSrcLabelInd
        self.sourceOptionsLabel.setText(f"Source {selectedSrcLabelInd+1}")


    def addOutputWidgets(self, sectionLayout):

        self.outputDirLayout = QHBoxLayout()
        self.inputLabel = QLabel("Output Directory")
        self.inputLabel.setStyleSheet(f"color: {TEXT_COLOR};")
        self.outputDirLayout.addWidget(self.inputLabel)
        self.outputDirLoc = QLineEdit()
        self.outputDirLoc.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR}; color: {TEXT_COLOR};")
        self.outputDirLoc.setTextMargins(5, 0, 0, 0)
        self.outputDirLoc.setReadOnly(True)
        self.outputDirLoc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.outputDirLayout.addWidget(self.outputDirLoc)

        self.inputBrowseBtn = QPushButton(text="Browse", parent=self.sourceLoc)
        self.inputBrowseBtn.setStyleSheet(f"background-color: {BUTTON_COLOR};color: {TEXT_COLOR};")
        self.outputDirLayout.addWidget(self.inputBrowseBtn, alignment = Qt.AlignmentFlag.AlignRight)
        self.inputBrowseBtn.clicked.connect(self.outputBrowseBtnClicked)

        sectionLayout.addLayout(self.outputDirLayout)

        self.outputFileOptionsLayout = QHBoxLayout()
        self.fileNameLabel = QLabel("File Name:")
        self.fileNameLabel.setStyleSheet(f"color: {TEXT_COLOR};")
        self.outputFileOptionsLayout.addWidget(self.fileNameLabel)
        self.fileNameTextField = QLineEdit()
        self.fileNameTextField.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR}; color: {TEXT_COLOR};")
        self.fileNameTextField.setTextMargins(5, 0, 0, 0)
        self.fileNameTextField.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.outputFileOptionsLayout.addWidget(self.fileNameTextField)

        self.frameDigLabel = QLabel("Frame Digits:")
        self.frameDigLabel.setStyleSheet(f"color: {TEXT_COLOR};")
        self.outputFileOptionsLayout.addWidget(self.frameDigLabel)

        self.frameDigDropdown = CustomComboBox(["3","4","5"])
        self.frameDigDropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.frameDigDropdown.activated.connect(self.on_frameDigit_selection_changed)
        self.outputFileOptionsLayout.addWidget(self.frameDigDropdown)

        sectionLayout.addLayout(self.outputFileOptionsLayout)

        self.fileFormatLayout = QHBoxLayout()
        self.fileFormatLabel = QLabel("File Name:")
        self.fileFormatLabel.setStyleSheet(f"color: {TEXT_COLOR};")
        self.fileFormatLayout.addWidget(self.fileFormatLabel)
        self.fileFormatDropdown = CustomComboBox(["JPEG","PNG","MP4", "AVI", "MOV"])
        self.fileFormatDropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.fileFormatDropdown.activated.connect(self.on_fileFormat_selection_changed)
        self.fileFormatLayout.addWidget(self.fileFormatDropdown)

        sectionLayout.addLayout(self.fileFormatLayout)

        self.fileProportionsLayout = QHBoxLayout()
        self.fileWidthLabel = QLabel("Width:")
        self.fileWidthLabel.setStyleSheet(f"color: {TEXT_COLOR};")
        self.fileProportionsLayout.addWidget(self.fileWidthLabel)
        self.fileWidth = QLineEdit()
        self.fileWidth.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR}; color: {TEXT_COLOR};")
        self.fileWidth.setTextMargins(5, 0, 0, 0)
        self.fileWidth.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.fileProportionsLayout.addWidget(self.fileWidth)

        self.fileHieghtLabel = QLabel("Height:")
        self.fileHieghtLabel.setStyleSheet(f"color: {TEXT_COLOR};")
        self.fileProportionsLayout.addWidget(self.fileHieghtLabel)
        self.fileHeight = QLineEdit()
        self.fileHeight.setStyleSheet(f"background-color: {TEXT_FIELD_COLOR}; color: {TEXT_COLOR};")
        self.fileHeight.setTextMargins(5, 0, 0, 0)
        self.fileHeight.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.fileProportionsLayout.addWidget(self.fileHeight)

        self.keepProportionsCheckbox = QCheckBox("Keep Proportions")
        # self.keepProportionsCheckbox = CustomIndicatorCheckBox("Keep Proportions")
        self.keepProportionsCheckbox.setEnabled(False)
        self.keepProportionsCheckbox.toggled.connect(self.on_checkbox_toggled)
        self.keepProportionsCheckbox.setStyleSheet(CHECKBOX_STYLESHEET)
        self.fileProportionsLayout.addWidget(self.keepProportionsCheckbox)

        sectionLayout.addLayout(self.fileProportionsLayout)

        self.convertBtn = QPushButton(text="Convert")
        self.convertBtn.setStyleSheet(BUTTON_STYLESHEET)
        sectionLayout.addWidget(self.convertBtn)
        self.convertBtn.clicked.connect(self.onConvertBtnClicked)


    def outputBrowseBtnClicked(self):
        folderPath= QFileDialog.getExistingDirectory(self, "Choose Directory","",QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks)
        if folderPath:
            self.outputDirLoc.setText(folderPath)


    def on_frameDigit_selection_changed(self, index):
        selected_text = self.frameDigDropdown.currentText()
        print(f"Selected: {selected_text} (Index: {index})")
        # You can update other widgets or perform actions here

    def on_fileFormat_selection_changed(self, index):
        selected_text = self.fileFormatDropdown.currentText()
        print(f"Selected: {selected_text} (Index: {index})")
        if selected_text not in ["JPEG","PNG"]:
            self.frameDigDropdown.setEnabled(False)
        else:
            self.frameDigDropdown.setEnabled(True)

    def on_checkbox_toggled(self, checked):
        if checked and self.fileWidth.text() and self.fileHeight.text():
            self.fileWidth.setReadOnly(True)
            self.fileHeight.setReadOnly(True)
        else:
            self.fileWidth.setReadOnly(False)
            self.fileHeight.setReadOnly(False)

    def setOutputDimensions(self, filePath):
        width,height = srcHnd.getSourceDimensions(filePath)
        print(width,height)
        if width is not None and height is not None:
            self.fileWidth.setText(f"{width}")
            print(width)
            self.fileHeight.setText(f"{height}")
            print(height)
            self.keepProportionsCheckbox.setEnabled(True)
            self.keepProportionsCheckbox.setChecked(True)


    def onConvertBtnClicked(self):
        conversionData = self.packageData()
        replace = True
        log = ""
        if conversionData["InputSources"] is not None: 
            outputFileExists = srcHnd.checkIfFileExists(conversionData["OutputDir"], conversionData["OutputFileName"], conversionData["OutputFormat"])
            if outputFileExists:
                replace = self.replace_File_dialog()
            if replace:
                log += srcHnd.convertMovie(conversionData)
            else:
                log += "Cancelled!"
            self.outputLogText.setText(log)
        else:
            self.msg = QMessageBox(self) # Pass self as parent for proper modality
            self.msg.setWindowTitle("Error")
            self.msg.setText("Please select input files to convert.")
            self.msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            result = self.msg.exec()
    

    def packageData(self):

        coversionData = {"InputSources":None, "OutputDir":"", "OutputFileName":"","OutputFormat": None, "OutputFrameDigits": None, "OuputWidth": None, "OuputHeight": None}
        inputSourceList = [src.filePath for src in self.sourceList if src.fileSelected]
        if inputSourceList:
            coversionData["InputSources"] = inputSourceList
            if self.outputDirLoc.text(): coversionData["OutputDir"] = self.outputDirLoc.text()
            if self.fileNameTextField.text: coversionData["OutputFileName"] = self.fileNameTextField.text()
            
            coversionData["OutputFormat"] = self.fileFormatDropdown.currentText()
            if self.frameDigDropdown.isEnabled() : coversionData["OutputFrameDigits"] = int(self.frameDigDropdown.currentText())
            if self.fileWidth.text() : coversionData["OuputWidth"] = int(self.fileWidth.text())
            if self.fileHeight.text() :  coversionData["OuputHeight"] = int(self.fileHeight.text())

        return coversionData

    def replace_File_dialog(self):
        # Create and show the question message box
        reply = QMessageBox.question(
            self,
            "Confirmation",  # Window title
            "A file with this name already exists.\nDo you want to replace it?",  # Message text
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, # Buttons
            QMessageBox.StandardButton.Cancel # Default button (optional)
        )

        # Process the user's reply
        if reply == QMessageBox.StandardButton.Yes:
            return True
        else:
            return False

def main():
    converMovieApp = QApplication(sys.argv)
    # converMovieApp.setStyle("Fusion")
    mainWindow = ConverMovieGUI()
    mainWindow.show()
    sys.exit(converMovieApp.exec())

if __name__ == "__main__":
    main()
