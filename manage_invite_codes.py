#!/usr/bin/env python3
"""
邀请码管理工具
用于创建、查看和管理邀请码
"""

import requests
import argparse
import json
from datetime import datetime
from tabulate import tabulate

# 默认服务器地址
DEFAULT_SERVER = "http://localhost:8000"

class InviteCodeManager:
    def __init__(self, server_url):
        self.server_url = server_url.rstrip('/')
    
    def list_codes(self):
        """列出所有邀请码"""
        try:
            response = requests.get(f"{self.server_url}/invite-codes")
            if response.status_code == 200:
                codes = response.json()["codes"]
                
                # 准备表格数据
                table_data = []
                for code in codes:
                    remaining = code['max_uses'] - code['used_count']
                    status = "有效" if remaining > 0 else "已用完"
                    
                    table_data.append([
                        code['code'],
                        f"{code['used_count']}/{code['max_uses']}",
                        remaining,
                        code['created_at'][:10] if code['created_at'] else "N/A",
                        code['expires_at'][:10] if code['expires_at'] else "永久",
                        status
                    ])
                
                # 打印表格
                headers = ["邀请码", "使用情况", "剩余次数", "创建日期", "过期日期", "状态"]
                print("\n邀请码列表:")
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                # 统计信息
                total_codes = len(codes)
                active_codes = sum(1 for c in codes if c['max_uses'] - c['used_count'] > 0)
                total_uses = sum(c['used_count'] for c in codes)
                
                print(f"\n统计信息:")
                print(f"  总邀请码数: {total_codes}")
                print(f"  有效邀请码: {active_codes}")
                print(f"  总使用次数: {total_uses}")
                
            else:
                print(f"获取邀请码失败: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"错误: {e}")
    
    def create_code(self, code, max_uses=30, expires_days=None):
        """创建新邀请码"""
        try:
            data = {
                "code": code,
                "max_uses": max_uses
            }
            
            if expires_days:
                data["expires_days"] = expires_days
            
            response = requests.post(
                f"{self.server_url}/invite-codes",
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 邀请码 '{code}' 创建成功")
                    print(f"   最大使用次数: {max_uses}")
                    if expires_days:
                        print(f"   有效期: {expires_days} 天")
                else:
                    print(f"❌ 创建失败: {result.get('message', '未知错误')}")
            elif response.status_code == 400:
                print(f"❌ 创建失败: 邀请码已存在")
            else:
                print(f"❌ 创建失败: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"错误: {e}")
    
    def batch_create(self, prefix, count, max_uses=30, expires_days=None):
        """批量创建邀请码"""
        print(f"批量创建 {count} 个邀请码...")
        
        success_count = 0
        for i in range(1, count + 1):
            code = f"{prefix}{i:04d}"
            try:
                data = {
                    "code": code,
                    "max_uses": max_uses
                }
                
                if expires_days:
                    data["expires_days"] = expires_days
                
                response = requests.post(
                    f"{self.server_url}/invite-codes",
                    json=data
                )
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"  ✅ {code}")
                else:
                    print(f"  ❌ {code} - 创建失败")
            
            except Exception as e:
                print(f"  ❌ {code} - 错误: {e}")
        
        print(f"\n完成! 成功创建 {success_count}/{count} 个邀请码")
    
    def export_codes(self, filename="invite_codes.json"):
        """导出邀请码数据"""
        try:
            response = requests.get(f"{self.server_url}/invite-codes")
            if response.status_code == 200:
                data = response.json()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 邀请码数据已导出到: {filename}")
            else:
                print(f"导出失败: HTTP {response.status_code}")
        
        except Exception as e:
            print(f"错误: {e}")

def main():
    parser = argparse.ArgumentParser(description="邀请码管理工具")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="服务器地址")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # list 命令
    subparsers.add_parser("list", help="列出所有邀请码")
    
    # create 命令
    create_parser = subparsers.add_parser("create", help="创建邀请码")
    create_parser.add_argument("code", help="邀请码")
    create_parser.add_argument("--max-uses", type=int, default=30, help="最大使用次数")
    create_parser.add_argument("--expires-days", type=int, help="有效天数")
    
    # batch 命令
    batch_parser = subparsers.add_parser("batch", help="批量创建邀请码")
    batch_parser.add_argument("prefix", help="邀请码前缀")
    batch_parser.add_argument("count", type=int, help="创建数量")
    batch_parser.add_argument("--max-uses", type=int, default=30, help="每个邀请码的最大使用次数")
    batch_parser.add_argument("--expires-days", type=int, help="有效天数")
    
    # export 命令
    export_parser = subparsers.add_parser("export", help="导出邀请码数据")
    export_parser.add_argument("--output", default="invite_codes.json", help="输出文件名")
    
    args = parser.parse_args()
    
    # 创建管理器
    manager = InviteCodeManager(args.server)
    
    # 执行命令
    if args.command == "list":
        manager.list_codes()
    
    elif args.command == "create":
        manager.create_code(
            args.code,
            args.max_uses,
            args.expires_days
        )
    
    elif args.command == "batch":
        manager.batch_create(
            args.prefix,
            args.count,
            args.max_uses,
            args.expires_days
        )
    
    elif args.command == "export":
        manager.export_codes(args.output)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()