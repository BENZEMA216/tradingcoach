"""
邮件服务

input: SMTP 配置, 邮件内容
output: 发送邮件
pos: 后端服务层 - 发送任务完成通知邮件

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
import smtplib
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务"""

    def __init__(self):
        """初始化邮件服务"""
        self.smtp_host = getattr(config, 'SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(config, 'SMTP_PORT', 587)
        self.smtp_user = getattr(config, 'SMTP_USER', '')
        self.smtp_password = getattr(config, 'SMTP_PASSWORD', '')
        self.from_email = getattr(config, 'SMTP_FROM_EMAIL', 'noreply@tradingcoach.com')
        self.from_name = getattr(config, 'SMTP_FROM_NAME', 'TradingCoach')

        self.enabled = bool(self.smtp_user and self.smtp_password)

        if not self.enabled:
            logger.warning("Email service disabled: SMTP credentials not configured")

    def is_configured(self) -> bool:
        """检查邮件服务是否已配置"""
        return self.enabled

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML 内容
            text_content: 纯文本内容（可选）

        Returns:
            是否发送成功
        """
        if not self.enabled:
            logger.warning(f"Email not sent (service disabled): {subject}")
            return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # 添加纯文本版本
            if text_content:
                msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

            # 添加 HTML 版本
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_analysis_complete(
        self,
        to_email: str,
        task_id: str,
        file_name: str,
        result: dict
    ) -> bool:
        """
        发送分析完成通知邮件

        Args:
            to_email: 收件人邮箱
            task_id: 任务ID
            file_name: 文件名
            result: 分析结果

        Returns:
            是否发送成功
        """
        subject = f"[TradingCoach] 分析完成 - {file_name}"

        # 提取结果数据
        new_trades = result.get('new_trades', 0)
        positions_matched = result.get('positions_matched', 0)
        positions_scored = result.get('positions_scored', 0)
        errors = result.get('errors', 0)

        # 生成 HTML 内容
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            flex: 1;
            min-width: 120px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border-radius: 6px;
            text-decoration: none;
            margin-top: 20px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>分析已完成</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">文件: {file_name}</p>
    </div>

    <div class="content">
        <p>您的交易数据已分析完成，以下是处理结果：</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{new_trades}</div>
                <div class="stat-label">交易记录</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{positions_matched}</div>
                <div class="stat-label">持仓配对</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{positions_scored}</div>
                <div class="stat-label">质量评分</div>
            </div>
        </div>

        {'<p style="color: #e74c3c;">处理过程中发现 ' + str(errors) + ' 个错误，请查看详情。</p>' if errors > 0 else ''}

        <div style="text-align: center;">
            <a href="http://localhost:5173/tasks/{task_id}" class="button">
                查看详细报告
            </a>
        </div>

        <p style="margin-top: 30px; font-size: 14px; color: #666;">
            任务ID: {task_id}
        </p>
    </div>

    <div class="footer">
        <p>此邮件由 TradingCoach 系统自动发送</p>
    </div>
</body>
</html>
"""

        # 纯文本版本
        text_content = f"""
TradingCoach - 分析完成通知

文件: {file_name}
任务ID: {task_id}

处理结果:
- 交易记录: {new_trades}
- 持仓配对: {positions_matched}
- 质量评分: {positions_scored}
{"- 错误数量: " + str(errors) if errors > 0 else ""}

访问 http://localhost:5173/tasks/{task_id} 查看详细报告。

---
此邮件由 TradingCoach 系统自动发送
"""

        return self.send_email(to_email, subject, html_content, text_content)

    def test_connection(self) -> tuple[bool, str]:
        """
        测试 SMTP 连接

        Returns:
            (是否成功, 消息)
        """
        if not self.enabled:
            return False, "SMTP 未配置，请设置 SMTP_USER 和 SMTP_PASSWORD"

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
            return True, "SMTP 连接成功"
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP 认证失败，请检查用户名和密码"
        except Exception as e:
            return False, f"SMTP 连接失败: {str(e)}"


# 全局邮件服务实例
email_service = EmailService()
