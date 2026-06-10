#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from waitress import serve
from app import app

if __name__ == '__main__':
    print("🚀 تشغيل خادم الراجحي للمحاسبة...")
    print("المنفذ: 8000")
    print("العنوان: 0.0.0.0")
    print("لإيقاف الخادم: Ctrl+C")
    try:
        serve(app, host='0.0.0.0', port=8000, threads=4)
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخادم.")
    except Exception as e:
        print(f"❌ خطأ: {e}")


