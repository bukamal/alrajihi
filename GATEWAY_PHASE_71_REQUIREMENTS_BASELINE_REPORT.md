# GATEWAY PHASE 71 - REQUIREMENTS BASELINE REPORT

## الهدف
تثبيت نقطة مستقرة للبناء اعتمادًا على Phase 70/Phase 65، وإضافة ملف `requirements.txt` الرسمي في جذر المشروع دون إدخال تعديلات Runtime جديدة على Qt أو الجداول.

## التعديلات المنفذة
- إضافة `requirements.txt` في جذر المشروع.
- إضافة أداة تحقق: `tools/verify_requirements_file.py`.
- تحديث GitHub Actions في `.github/workflows/build-windows-installer.yml` لإضافة خطوة تحقق من ملف المتطلبات.

## المتطلبات المضافة
- PyQt5
- qt-material
- pyqtgraph
- qtawesome
- openpyxl
- reportlab
- qrcode
- Pillow
- python-barcode
- cryptography
- requests
- pyserial
- opencv-python
- pyzbar
- Flask
- Flask-JWT-Extended
- waitress
- Werkzeug

## حدود المرحلة
لم يتم في هذه المرحلة:
- إعادة تفعيل Runtime EventFilter للجداول.
- إضافة أي QtWebEngine flags.
- تعديل شاشة الدخول أو لوحة التحكم أو الطباعة.
- تغيير QSS خارج ما كان موجودًا في النسخة المستقرة.

## الاختبارات
- `python3 tools/verify_requirements_file.py`
- `python3 -m compileall -q alrajhi_client tools`

## النتيجة
المرحلة مستقرة كقاعدة بناء، وتعالج خطأ غياب `requirements.txt` في GitHub Actions.
