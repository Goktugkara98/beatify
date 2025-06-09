import sys
import json
import copy  # YENİ EKLENEN KISIM: Derin kopyalama için gereklidir.
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar,
                             QStatusBar, QFileDialog, QLineEdit, QLabel, QHBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QPushButton, QDialog,
                             QFormLayout, QDialogButtonBox, QMessageBox, QInputDialog, QComboBox, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

# Öğe eklemek için özel diyalog kutusu
class AddItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Öğe Ekle")

        self.layout = QFormLayout(self)

        self.key_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Değer (Metin/Sayı)", "Yeni Nesne (Sınıf)", "Yeni Liste"])
        self.value_input = QLineEdit()

        self.layout.addRow("Anahtar:", self.key_input)
        self.layout.addRow("Tür:", self.type_combo)
        self.layout.addRow("Değer:", self.value_input)

        self.type_combo.currentIndexChanged.connect(self.update_value_input_state)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)
        self.update_value_input_state() # Başlangıç durumunu ayarla

    def update_value_input_state(self):
        # Sadece "Değer" seçiliyse değer giriş kutusunu aktif et
        is_value_type = self.type_combo.currentText() == "Değer (Metin/Sayı)"
        self.value_input.setEnabled(is_value_type)

    def get_data(self):
        key = self.key_input.text()
        item_type = self.type_combo.currentText()
        value = self.value_input.text()
        return key, item_type, value

# Anahtar-değer düzenlemek için özel diyalog kutusu
class EditDialog(QDialog):
    def __init__(self, key, value, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Öğe Düzenle")
        self.original_value = value # Orijinal değeri tip kontrolü için sakla

        self.layout = QFormLayout(self)

        self.key_input = QLineEdit(key)
        
        # DEĞİŞTİRİLEN KISIM: Anahtarın (listelerde index olduğu için) düzenlenmesini engelle
        is_in_list = False
        try:
            int(key) # Eğer anahtar sayıya çevrilebiliyorsa, bir liste indeksi olabilir
            is_in_list = True
        except (ValueError, TypeError):
            is_in_list = False

        if is_in_list:
            self.key_input.setReadOnly(True)


        if isinstance(value, dict):
            self.value_input = QLabel("(Sözlük/Nesne)")
        elif isinstance(value, list):
            self.value_input = QLabel("(Liste)")
        else:
            self.value_input = QLineEdit(str(value))

        self.layout.addRow("Anahtar:", self.key_input)
        self.layout.addRow("Değer:", self.value_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.button_box)

    def get_data(self):
        key = self.key_input.text()
        value_text = self.value_input.text() if isinstance(self.value_input, QLineEdit) else self.original_value
        
        # Değeri orijinal tipine dönüştürmeye çalış
        if not isinstance(value_text, (dict, list)):
            try:
                # Orijinal değerin tipini kontrol ederek doğru dönüşümü yap
                original_type = type(self.original_value)
                if original_type is int:
                    return key, int(value_text)
                if original_type is float:
                    return key, float(value_text)
                if original_type is bool:
                    # 'true'/'false' gibi metinleri boolean'a çevir
                    if value_text.lower() in ['true', '1', 'evet']:
                        return key, True
                    if value_text.lower() in ['false', '0', 'hayır']:
                        return key, False
            except (ValueError, TypeError):
                pass # Dönüşüm başarısız olursa string olarak bırak
        
        return key, value_text

class JsonEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gelişmiş JSON Editörü")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.data = {}
        self.current_file = None

        self.init_ui()

    def init_ui(self):
        self.create_menu_bar()
        self.create_status_bar()
        self.create_main_layout()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Dosya")

        open_action = QAction("Aç...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Kaydet", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Farklı Kaydet...", self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def create_status_bar(self):
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Hazır")

    def create_main_layout(self):
        # DEĞİŞTİRİLEN KISIM: Yeni butonlar eklendi
        buttons_layout = QHBoxLayout()
        add_button = QPushButton("Öğe Ekle")
        add_button.clicked.connect(self.add_item)
        buttons_layout.addWidget(add_button)

        copy_button = QPushButton("Öğe Kopyala") # YENİ
        copy_button.clicked.connect(self.copy_item) # YENİ
        buttons_layout.addWidget(copy_button) # YENİ

        edit_button = QPushButton("Öğe Düzenle")
        edit_button.clicked.connect(self.edit_item)
        buttons_layout.addWidget(edit_button)

        delete_button = QPushButton("Öğe Sil")
        delete_button.clicked.connect(self.delete_item)
        buttons_layout.addWidget(delete_button)

        move_up_button = QPushButton("Yukarı Taşı") # YENİ
        move_up_button.clicked.connect(self.move_item_up) # YENİ
        buttons_layout.addWidget(move_up_button) # YENİ
        
        move_down_button = QPushButton("Aşağı Taşı") # YENİ
        move_down_button.clicked.connect(self.move_item_down) # YENİ
        buttons_layout.addWidget(move_down_button) # YENİ

        self.layout.addLayout(buttons_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Anahtar", "Değer"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.itemDoubleClicked.connect(self.edit_item)
        self.layout.addWidget(self.tree)

    def get_expanded_state(self, item, path=None, state=None):
        if path is None:
            path = [item.text(0)]
        if state is None:
            state = {}
        state[tuple(path)] = item.isExpanded()
        for i in range(item.childCount()):
            child = item.child(i)
            self.get_expanded_state(child, path + [child.text(0)], state)
        return state

    def set_expanded_state(self, item, path=None, state=None):
        if path is None:
            path = [item.text(0)]
        if state is None:
            return
        if tuple(path) in state:
            item.setExpanded(state[tuple(path)])
        for i in range(item.childCount()):
            child = item.child(i)
            self.set_expanded_state(child, path + [child.text(0)], state)

    def load_data_to_ui(self, selected_path=None):
        if selected_path is None and self.tree.currentItem() is not None:
            selected_path = self._get_path_from_selected_item()

        expanded_state = {}
        if self.tree.topLevelItemCount() > 0:
            expanded_state = self.get_expanded_state(self.tree.topLevelItem(0))
        
        self.tree.clear()
        root_item = QTreeWidgetItem(["JSON", ""])
        self.tree.addTopLevelItem(root_item)
        self._populate_tree(root_item, self.data)
        
        self.set_expanded_state(root_item, state=expanded_state)
        
        if selected_path:
            if selected_path == ["JSON"]:
                self.tree.setCurrentItem(root_item)
            else:
                item_to_select = self._get_item_from_path(selected_path)
                if item_to_select:
                    self.tree.setCurrentItem(item_to_select)
                    item_to_select.setSelected(True)


    def _populate_tree(self, parent_item, data):
        if isinstance(data, dict):
            for key, value in data.items():
                child_item = QTreeWidgetItem([str(key), "" if isinstance(value, (dict, list)) else str(value)])
                parent_item.addChild(child_item)
                if isinstance(value, (dict, list)):
                    self._populate_tree(child_item, value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                item_text = f"[{index}]"
                child_item = QTreeWidgetItem([item_text, "" if isinstance(value, (dict, list)) else str(value)])
                parent_item.addChild(child_item)
                if isinstance(value, (dict, list)):
                    self._populate_tree(child_item, value)

    def _get_item_from_path(self, path, parent_item=None):
        if parent_item is None:
            parent_item = self.tree.topLevelItem(0)
        
        current_item = parent_item
        # 'JSON' kökünü atla, path[1:] ile başla
        for part in path[1:]:
            found_child = None
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                child_key = child.text(0)
                # Hem dict anahtarı (str) hem de list indeksi ([int]) ile eşleşme kontrolü
                if child_key == str(part) or child_key == f"[{part}]":
                    found_child = child
                    break
            if found_child:
                current_item = found_child
            else:
                return None # Yol bulunamadı
        return current_item

    
    def _get_data_and_parent_from_path(self, path):
        # ['JSON', 'users', 0] gibi bir yolda, 'users' listesini ve [0] öğesini bulur.
        # Bu fonksiyon, son öğenin ait olduğu veri yapısını (parent_data) ve o öğenin kendisini (data) döndürür.
        if not path or path == ["JSON"]:
            return self.data, None # Kök için ebeveyn yok

        parent_data = self.data
        for key in path[1:-1]: # Son anahtar hariç yolda ilerle
            if isinstance(parent_data, list):
                parent_data = parent_data[int(key)]
            else:
                parent_data = parent_data[key]

        last_key = path[-1]
        if isinstance(parent_data, list):
            data = parent_data[int(last_key)]
        else:
            data = parent_data[last_key]
        
        return data, parent_data

    
    def _get_path_from_selected_item(self):
        item = self.tree.currentItem()
        if not item:
            return None
        
        path = []
        temp_item = item
        while temp_item is not None:
            key_text = temp_item.text(0)
            parent = temp_item.parent()
            
            if parent is not None:
                # Liste indekslerini sayı olarak, dict anahtarlarını metin olarak al
                if key_text.startswith('[') and key_text.endswith(']'):
                    try:
                        idx = int(key_text[1:-1])
                        path.insert(0, idx)
                    except ValueError:
                        path.insert(0, key_text) # Hata durumunda metin olarak kalsın
                else:
                    path.insert(0, key_text)
            else:
                path.insert(0, "JSON") # Kök öğe

            temp_item = parent
        return path

    def add_item(self):
        selected_item = self.tree.currentItem()
        # DEĞİŞİKLİK: Eğer hiçbir şey seçili değilse veya kök seçiliyse, doğrudan ana veriye ekle
        if not selected_item or selected_item.text(0) == "JSON":
            current_data = self.data
            path = ["JSON"]
        else:
            path = self._get_path_from_selected_item()
            current_data, _ = self._get_data_and_parent_from_path(path)

        dialog = AddItemDialog(self)
        if dialog.exec():
            key, item_type, value = dialog.get_data()
            new_value = None
            if item_type == "Yeni Nesne (Sınıf)":
                new_value = {}
            elif item_type == "Yeni Liste":
                new_value = []
            else:
                try: new_value = int(value)
                except ValueError:
                    try: new_value = float(value)
                    except ValueError: new_value = value

            if isinstance(current_data, dict):
                if not key:
                    QMessageBox.warning(self, "Hata", "Anahtar boş olamaz.")
                    return
                if key in current_data:
                    QMessageBox.warning(self, "Hata", "Bu anahtar zaten mevcut.")
                    return
                current_data[key] = new_value
                self.load_data_to_ui(path + [key])
                self.statusBar().showMessage(f"'{key}' anahtarı eklendi.")
            elif isinstance(current_data, list):
                current_data.append(new_value)
                self.load_data_to_ui(path + [len(current_data)-1])
                self.statusBar().showMessage("Listeye yeni öğe eklendi.")
            else:
                QMessageBox.warning(self, "Hata", "Öğe yalnızca bir nesneye (dict) veya listeye eklenebilir.")

    # =======================================================================
    # YENİ EKLENEN KISIM: Kopyalama ve Taşıma Fonksiyonları
    # =======================================================================
    def copy_item(self):
        path = self._get_path_from_selected_item()
        if not path or path == ["JSON"]:
            QMessageBox.warning(self, "Uyarı", "Kök öğe kopyalanamaz. Lütfen bir alt öğe seçin.")
            return

        data_to_copy, parent_data = self._get_data_and_parent_from_path(path)
        cloned_data = copy.deepcopy(data_to_copy) # İç içe nesneler için derin kopyalama

        new_path = []
        if isinstance(parent_data, dict):
            original_key = path[-1]
            new_key = f"{original_key}_copy"
            # Eğer aynı isimde kopya varsa, sonuna sayı ekle (_copy_2, _copy_3...)
            i = 2
            while new_key in parent_data:
                new_key = f"{original_key}_copy_{i}"
                i += 1
            parent_data[new_key] = cloned_data
            new_path = path[:-1] + [new_key]
            self.statusBar().showMessage(f"'{original_key}' öğesi '{new_key}' olarak kopyalandı.")

        elif isinstance(parent_data, list):
            original_index = path[-1]
            parent_data.insert(original_index + 1, cloned_data)
            new_path = path[:-1] + [original_index + 1]
            self.statusBar().showMessage(f"'{original_index}' indeksindeki öğe kopyalandı.")
        
        else:
            QMessageBox.warning(self, "Hata", "Beklenmedik bir durum oluştu.")
            return
        
        self.load_data_to_ui(new_path)


    def move_item_up(self):
        path = self._get_path_from_selected_item()
        if not path or path == ["JSON"]:
            QMessageBox.warning(self, "Uyarı", "Lütfen taşımak için bir öğe seçin.")
            return
        
        _, parent_data = self._get_data_and_parent_from_path(path)
        index_or_key = path[-1]

        if isinstance(parent_data, list):
            index = index_or_key
            if index > 0:
                parent_data.insert(index - 1, parent_data.pop(index))
                new_path = path[:-1] + [index - 1]
                self.load_data_to_ui(new_path)
                self.statusBar().showMessage(f"Öğe yukarı taşındı.")
            else:
                self.statusBar().showMessage(f"Öğe zaten en üstte.")
        elif isinstance(parent_data, dict):
            keys = list(parent_data.keys())
            try:
                idx = keys.index(index_or_key)
            except ValueError:
                self.statusBar().showMessage(f"Anahtar bulunamadı.")
                return
            if idx > 0:
                # Anahtarı bir öncekiyle yer değiştir
                keys[idx - 1], keys[idx] = keys[idx], keys[idx - 1]
                new_dict = {k: parent_data[k] for k in keys}
                parent_data.clear()
                parent_data.update(new_dict)
                new_path = path[:-1] + [keys[idx - 1]]
                self.load_data_to_ui(new_path)
                self.statusBar().showMessage(f"Anahtar yukarı taşındı.")
            else:
                self.statusBar().showMessage(f"Anahtar zaten en üstte.")
        else:
            QMessageBox.information(self, "Bilgi", "Taşıma işlemi yalnızca sözlük veya listelerdeki öğeler için geçerlidir.")
            return

    def move_item_down(self):
        path = self._get_path_from_selected_item()
        if not path or path == ["JSON"]:
            QMessageBox.warning(self, "Uyarı", "Lütfen taşımak için bir öğe seçin.")
            return
        
        _, parent_data = self._get_data_and_parent_from_path(path)
        index_or_key = path[-1]

        if isinstance(parent_data, list):
            index = index_or_key
            if index < len(parent_data) - 1:
                parent_data.insert(index + 1, parent_data.pop(index))
                new_path = path[:-1] + [index + 1]
                self.load_data_to_ui(new_path)
                self.statusBar().showMessage(f"Öğe aşağı taşındı.")
            else:
                self.statusBar().showMessage(f"Öğe zaten en altta.")
        elif isinstance(parent_data, dict):
            keys = list(parent_data.keys())
            try:
                idx = keys.index(index_or_key)
            except ValueError:
                self.statusBar().showMessage(f"Anahtar bulunamadı.")
                return
            if idx < len(keys) - 1:
                # Anahtarı bir sonrakiyle yer değiştir
                keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]
                new_dict = {k: parent_data[k] for k in keys}
                parent_data.clear()
                parent_data.update(new_dict)
                new_path = path[:-1] + [keys[idx + 1]]
                self.load_data_to_ui(new_path)
                self.statusBar().showMessage(f"Anahtar aşağı taşındı.")
            else:
                self.statusBar().showMessage(f"Anahtar zaten en altta.")
        else:
            QMessageBox.information(self, "Bilgi", "Taşıma işlemi yalnızca sözlük veya listelerdeki öğeler için geçerlidir.")
            return

    # =======================================================================
    # Mevcut Fonksiyonlardaki İyileştirmeler
    # =======================================================================

    def edit_item(self):
        path = self._get_path_from_selected_item()
        if not path:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek için bir öğe seçin.")
            return
        if path == ["JSON"]:
            QMessageBox.warning(self, "Uyarı", "Kök (JSON) öğesi düzenlenemez.")
            return

        original_data, parent_data = self._get_data_and_parent_from_path(path)
        key_to_edit = path[-1]

        # Nesne ve listelerin sadece anahtar adını düzenle, değeri için uyar
        if isinstance(original_data, (dict, list)) and isinstance(parent_data, dict):
             QMessageBox.information(self, "Bilgi", "Nesne veya listelerin içeriğini doğrudan düzenlemek için lütfen içindeki öğeleri tek tek düzenleyin. Bu ekranda sadece anahtar adını değiştirebilirsiniz.")

        dialog = EditDialog(str(key_to_edit), original_data, self)
        if dialog.exec():
            new_key_str, new_value = dialog.get_data()

            # Değişiklikleri ana veri yapısına uygula
            if isinstance(parent_data, dict):
                original_key = path[-1]
                # Anahtar adı değişti mi?
                if new_key_str != str(original_key):
                    if new_key_str in parent_data:
                        QMessageBox.warning(self, "Hata", "Bu anahtar adı zaten kullanılıyor.")
                        return
                    # Eski anahtarı silip yenisiyle veriyi tekrar ekle (sırayı korumak için)
                    items = list(parent_data.items())
                    index = list(parent_data.keys()).index(original_key)
                    items[index] = (new_key_str, original_data) # Sadece anahtarı değiştir, değeri koru
                    parent_data.clear()
                    parent_data.update(items)
                    path[-1] = new_key_str # Yolu güncelle
                
                # Değeri güncelle (eğer basit bir tip ise)
                if not isinstance(original_data, (dict, list)):
                     parent_data[new_key_str] = new_value

            elif isinstance(parent_data, list):
                # Listelerde sadece değer güncellenir, anahtar (index) değişmez
                index = path[-1]
                parent_data[index] = new_value

            self.load_data_to_ui(path)
            self.statusBar().showMessage(f"'{path[-1]}' güncellendi.")

    def delete_item(self):
        path = self._get_path_from_selected_item()
        if not path:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için bir öğe seçin.")
            return
        if path == ["JSON"]:
            QMessageBox.warning(self, "Uyarı", "Kök (JSON) öğesi silinemez.")
            return
            
        key_to_delete = path[-1]
        reply = QMessageBox.question(self, "Öğe Sil", f"'{key_to_delete}' öğesini ve tüm içeriğini silmek istediğinizden emin misiniz?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            _, parent_data = self._get_data_and_parent_from_path(path)
            
            # Silme işlemini ebeveynin türüne göre yap (dict veya list)
            if isinstance(parent_data, dict):
                del parent_data[key_to_delete]
            elif isinstance(parent_data, list):
                del parent_data[int(key_to_delete)]
            
            self.load_data_to_ui(path[:-1]) # Bir üst öğeyi seçili bırak
            self.statusBar().showMessage(f"'{key_to_delete}' silindi.")


    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "JSON Dosyası Aç", "", "JSON Dosyaları (*.json);;Tüm Dosyalar (*)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                self.current_file = file_name
                self.statusBar().showMessage(f"'{file_name}' yüklendi.")
                self.load_data_to_ui(["JSON"]) # Kökü seçili başlat
            except Exception as e:
                self.statusBar().showMessage(f"Hata: Dosya yüklenemedi - {e}")
                self.data = {}
                self.load_data_to_ui()

    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=4, ensure_ascii=False)
                self.statusBar().showMessage(f"'{self.current_file}' kaydedildi.")
            except Exception as e:
                self.statusBar().showMessage(f"Hata: Dosya kaydedilemedi - {e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "JSON Dosyasını Kaydet", "", "JSON Dosyaları (*.json);;Tüm Dosyalar (*)")
        if file_name:
            if not file_name.endswith('.json'):
                file_name += '.json'
                
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=4, ensure_ascii=False)
                self.current_file = file_name
                self.statusBar().showMessage(f"'{file_name}' olarak kaydedildi.")
            except Exception as e:
                self.statusBar().showMessage(f"Hata: Dosya kaydedilemedi - {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = JsonEditorApp()
    editor.show()
    sys.exit(app.exec())