# -*- coding: utf-8 -*-
"""
Weverse Shop Plush Toy 补货监控脚本
商品页面: https://shop.weverse.io/zh-cn/shop/KRW/artists/7/sales/42410

使用方法:
    python weverse_monitor.py                    # 单次检查
    python weverse_monitor.py --loop --interval 300  # 循环检查,每300秒一次
    python weverse_monitor.py --loop --interval 60 --beep  # 循环检查,补货时蜂鸣提醒
    python weverse_monitor.py --loop --interval 60 --email # 循环检查,补货时发送邮件
"""

import sys
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime

# ======================== 商品配置 ========================
TARGET_URL = "https://shop.weverse.io/zh-cn/shop/KRW/artists/7/sales/42410"
PRODUCT_NAME = "SEVENTEEN Plush Toy"

# ======================== 邮件配置 ========================
# 敏感信息优先从环境变量读取(GitHub Actions Secrets),本地也可直接填写
EMAIL_CONFIG = {
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.qq.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "465")),
    "sender_email": os.environ.get("SENDER_EMAIL", "2910233855@qq.com"),
    "sender_name": os.environ.get("SENDER_NAME", "Weverse补货监控"),
    "email_password": os.environ.get("EMAIL_PASSWORD", ""),  # QQ邮箱 SMTP 授权码
    "receiver_email": os.environ.get("RECEIVER_EMAIL", "2910233855@qq.com"),
}
# ==========================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def beep():
    """播放提示音 (Windows)"""
    try:
        import winsound
        winsound.Beep(800, 500)
        time.sleep(0.2)
        winsound.Beep(1000, 500)
        time.sleep(0.2)
        winsound.Beep(800, 500)
    except ImportError:
        print("\a")


def send_email():
    """
    发送补货通知邮件 (QQ 邮箱 SMTP)
    需要在 EMAIL_CONFIG 中填入 email_password (SMTP 授权码)
    """
    if not EMAIL_CONFIG.get("email_password"):
        print("  ⚠️ 邮件授权码未配置,跳过邮件发送")
        print("     请编辑脚本中的 EMAIL_CONFIG['email_password']")
        print("     获取方法: QQ邮箱网页版 → 设置 → 账户 → 开启SMTP服务")
        return False
    
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建邮件
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Weverse 补货通知 - {PRODUCT_NAME}"
        # 使用 formataddr 正确处理中文发件人名称 (RFC2047 编码)
        msg["From"] = formataddr((str(Header(EMAIL_CONFIG["sender_name"], "utf-8")), EMAIL_CONFIG["sender_email"]))
        msg["To"] = EMAIL_CONFIG["receiver_email"]
        
        # 纯文本版本
        text_content = f"""
🎉🎉🎉 商品补货通知! 🎉🎉🎉

商品: {PRODUCT_NAME}
时间: {now}
链接: {TARGET_URL}

操作提示:
1. 立即访问上面的链接
2. 登录 Weverse 账号
3. 将 KIMJA 加入购物车,数量设置为 2
4. 快速结算!

祝您购物愉快!
—— Weverse 补货监控脚本
"""
        
        # HTML 版本
        html_content = f"""
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: "Microsoft YaHei", Arial, sans-serif; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #00CBD5, #00a0a8); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }}
  .body {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #eee; }}
  .product {{ font-size: 20px; font-weight: bold; color: #333; margin-bottom: 15px; }}
  .time {{ color: #666; margin-bottom: 20px; }}
  .link {{ display: inline-block; background: #00CBD5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 15px 0; font-weight: bold; }}
  .steps {{ margin-top: 25px; padding: 20px; background: #fff; border-radius: 8px; border-left: 4px solid #00CBD5; }}
  .steps p {{ margin: 8px 0; color: #555; }}
  .footer {{ text-align: center; margin-top: 20px; color: #999; font-size: 12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2>🎉 商品补货通知 🎉</h2>
  </div>
  <div class="body">
    <div class="product">{PRODUCT_NAME}</div>
    <div class="time">补货时间: {now}</div>
    <a href="{TARGET_URL}" class="link">👉 立即前往购买</a>
    <div class="steps">
      <p><strong>🛒 操作步骤:</strong></p>
      <p>1️⃣ 点击上方链接访问商品页面</p>
      <p>2️⃣ 登录 Weverse 账号</p>
      <p>3️⃣ 将 KIMJA 加入购物车,数量设置为 <strong>2</strong></p>
      <p>4️⃣ 快速结算! (限购 3 个)</p>
    </div>
    <p class="footer">— Weverse 补货监控脚本自动发送</p>
  </div>
</div>
</body>
</html>
"""
        
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        # 发送邮件 (SSL)
        print("  📧 正在发送邮件通知...")
        with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"], timeout=30) as server:
            server.set_debuglevel(0)  # 设为 1 可看调试信息
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["email_password"])
            server.sendmail(
                EMAIL_CONFIG["sender_email"],
                [EMAIL_CONFIG["receiver_email"]],
                msg.as_string()
            )
        
        print("  ✅ 邮件发送成功!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"  ❌ 邮件发送失败: 授权码错误或SMTP未开启 ({e})")
        print("     请检查: 1. SMTP服务是否开启  2. 授权码是否正确(不是QQ密码)")
        return False
    except smtplib.SMTPException as e:
        print(f"  ❌ 邮件发送失败: SMTP错误 ({e})")
        return False
    except Exception as e:
        print(f"  ❌ 邮件发送失败: {e}")
        return False


def fetch_url(url, headers=None, timeout=30):
    """获取 URL 内容"""
    try:
        req = Request(url, headers=headers or HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (URLError, HTTPError, TimeoutError) as e:
        return None
    except Exception as e:
        return None


def check_stock_status():
    """
    检查库存状态
    返回: (是否有货, 详细信息)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 方法1: 检查 HTML 页面
    content = fetch_url(TARGET_URL)
    
    if content is None:
        return False, f"[{timestamp}] 无法访问网站"
    
    # 检查售罄标志
    sold_out_indicators = [
        '售罄',           # 中文售罄文本
        'sold out',       # 英文售罄
        'disabled',       # 按钮禁用
        'name="checkout"', # 购物车按钮名称
    ]
    
    # 计算售罄标志出现次数
    sold_out_count = 0
    for indicator in sold_out_indicators:
        if indicator.lower() in content.lower():
            sold_out_count += 1
    
    # 检查是否有"加入购物车"或购买按钮
    has_add_to_cart = any(kw in content.lower() for kw in [
        '加入购物车',
        'add to cart',
        'cart',
        '구매하기',  # 韩语"购买"
    ])
    
    # 检查是否有 disabled 的 checkout 按钮 (最可靠的售罄标志)
    checkout_disabled = 'checkout' in content.lower() and 'disabled' in content.lower()
    
    # 判断逻辑
    # 如果 checkout_disabled 为 True,则肯定是售罄
    # 如果有"售罄"文本,也是售罄
    is_sold_out = checkout_disabled or '售罄' in content
    
    if not is_sold_out and has_add_to_cart:
        return True, f"[{timestamp}] *** 商品可能已补货! ***"
    elif is_sold_out:
        return False, f"[{timestamp}] 仍在售罄中 (checkout_disabled={checkout_disabled})"
    else:
        # 不确定状态,保守起见认为在售罄
        return False, f"[{timestamp}] 状态不确定,保守认为在售罄 (sold_out_count={sold_out_count})"


def main():
    args = sys.argv[1:]
    loop = "--loop" in args
    interval = 60  # 默认60秒
    beep_on_find = "--beep" in args
    email_on_find = "--email" in args
    
    # 解析间隔
    if "--interval" in args:
        idx = args.index("--interval")
        if idx + 1 < len(args):
            interval = int(args[idx + 1])
    
    print(f"=" * 60)
    print(f"Weverse Shop {PRODUCT_NAME} 补货监控")
    print(f"目标页面: {TARGET_URL}")
    print(f"模式: {'循环监控 (每 ' + str(interval) + ' 秒)' if loop else '单次检查'}")
    
    # 通知方式
    notify_methods = []
    if beep_on_find:
        notify_methods.append("🔔 蜂鸣提醒")
    if email_on_find:
        notify_methods.append("📧 邮件通知")
    if not notify_methods:
        notify_methods.append("💬 仅控制台输出")
    print(f"通知方式: {', '.join(notify_methods)}")
    
    if email_on_find and not EMAIL_CONFIG.get("email_password"):
        print(f"⚠️  邮件通知已启用,但授权码未配置!")
        print(f"   请编辑 EMAIL_CONFIG['email_password']")
        print(f"=" * 60)
        print()
        # 先测试一次邮件发送,让用户看到错误提示
        print("[测试] 尝试发送邮件...")
        send_email()
        print()
        return  # 授权码未配置时直接退出,避免空跑
    
    print(f"=" * 60)
    
    check_count = 0
    notification_sent = False  # 防止重复通知
    
    while True:
        check_count += 1
        in_stock, message = check_stock_status()
        
        if in_stock:
            print(f"\n{'=' * 60}")
            print(f"🎉 {message}")
            print(f"🔗 立即访问: {TARGET_URL}")
            print(f"   将 KIMJA 加入购物车,数量设置为 2")
            print(f"{'=' * 60}\n")
            
            if beep_on_find and not notification_sent:
                print("  🔔 播放提示音...")
                beep()
            
            if email_on_find and not notification_sent:
                send_email()
            
            notification_sent = True  # 标记已通知,防止重复发送
            
            if not loop:
                break
            # 循环模式下,通知一次后继续监控(等下次又变成售罄)
            time.sleep(interval)
        else:
            print(f"[{check_count}] {message}", end="")
            if loop:
                print(f" - {interval}秒后再次检查...")
                # 已通知过且又变回售罄状态,重置标记以便下次补货时再次通知
                if notification_sent:
                    notification_sent = False
                    print("    ↩️  已重置通知标记,下次补货时会再次通知")
            else:
                print()
        
        if not loop:
            break
        
        time.sleep(interval)


if __name__ == "__main__":
    main()
