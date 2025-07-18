#!/usr/bin/env python3
"""测试导入问题"""

print("开始导入测试...")

try:
    print("1. 导入 RegisterDialog...")
    from auth_module.register_dialog import RegisterDialog
    print("   成功!")
except Exception as e:
    print(f"   失败: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. 导入 ForgotPasswordDialog...")
    from auth_module.forgot_password_dialog import ForgotPasswordDialog  
    print("   成功!")
except Exception as e:
    print(f"   失败: {e}")
    import traceback
    traceback.print_exc()

print("\n导入测试完成。")