"""
初始化数据库和默认数据
- 创建所有表
- 插入默认管理员 admin/123456
- 插入示例商品知识数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, SessionLocal
from app.models.user import User
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from app.utils.security import hash_password
from app.config import settings


def create_admin():
    """创建默认管理员账号（随机密码，首次运行时打印到控制台）"""
    import secrets
    db = SessionLocal()
    try:
        # 检查是否已存在
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("[初始化] 管理员账号已存在，跳过")
            return

        # 生成 8 位随机密码（含大小写字母+数字）
        random_password = secrets.token_urlsafe(8)
        admin = User(
            username="admin",
            password_hash=hash_password(random_password),
            role="admin",
        )
        db.add(admin)
        db.commit()
        print(f"[初始化] 管理员账号创建成功: admin / {random_password}")
        print("[警告] 请记录此密码并登录后及时修改！")
    finally:
        db.close()


def create_sample_knowledge():
    """创建示例商品知识数据"""
    db = SessionLocal()
    try:
        # 检查是否已有数据
        count = db.query(KnowledgeDocument).count()
        if count > 0:
            print(f"[初始化] 知识库已有 {count} 条数据，跳过示例数据")
            return

        # 示例商品知识
        sample_docs = [
            {
                "title": "iPhone 15 Pro 产品说明",
                "content": """iPhone 15 Pro 产品说明

品牌：Apple
型号：iPhone 15 Pro
发布日期：2023年9月

【核心参数】
- 芯片：A17 Pro 芯片，3纳米工艺
- 屏幕：6.1英寸 Super Retina XDR OLED，120Hz ProMotion
- 存储：128GB / 256GB / 512GB / 1TB
- 后置摄像头：4800万像素主摄 + 1200万像素超广角 + 1200万像素长焦
- 前置摄像头：1200万像素原深感摄像头
- 电池：3274mAh，支持20W有线快充，15W MagSafe无线充电
- 材质：钛金属边框，亚光质感玻璃背板
- 重量：187克
- 系统：iOS 17
- 颜色：原色钛金属、蓝色钛金属、白色钛金属、黑色钛金属

【价格】
- 128GB：7999元
- 256GB：8999元
- 512GB：10999元
- 1TB：12999元

【主要特性】
- 操作按钮：可自定义功能（静音、相机、手电筒等）
- USB-C接口：支持USB 3，传输速度最高10Gb/s
- 5G网络：支持Sub-6GHz和毫米波
- 防水等级：IP68
- 卫星通信：支持紧急SOS卫星求救

【售后服务】
- 7天无理由退货
- 1年有限保修
- 可购买AppleCare+延保服务（2年）
- 全国Apple Store及授权服务商网点维修""",
                "file_type": "txt",
            },
            {
                "title": "华为Mate 60 Pro 产品说明",
                "content": """华为Mate 60 Pro 产品说明

品牌：华为 (HUAWEI)
型号：Mate 60 Pro
发布日期：2023年8月

【核心参数】
- 芯片：麒麟9000S，支持卫星通话
- 屏幕：6.82英寸 OLED 曲面屏，120Hz刷新率，1440Hz高频PWM调光
- 存储：256GB / 512GB / 1TB
- 运行内存：12GB
- 后置摄像头：5000万像素超光变主摄 + 1200万像素超广角 + 4800万像素长焦微距
- 前置摄像头：1300万像素 + 3D深感摄像头
- 电池：5000mAh，支持88W有线快充，50W无线快充
- 材质：第二代昆仑玻璃，金属中框
- 重量：约225克
- 系统：HarmonyOS 4.0
- 颜色：雅川青、白沙银、南糯紫、雅丹黑

【价格】
- 256GB + 12GB：6999元
- 512GB + 12GB：7999元
- 1TB + 12GB：8999元

【主要特性】
- 卫星通话：全球首款支持卫星通话的大众智能手机
- 鸿蒙生态：多设备协同、超级中转站
- 防水等级：IP68
- AI隔空操控
- 智感支付

【售后服务】
- 7天无理由退货
- 1年主机保修
- 华为客服热线：950800
- 全国华为授权服务中心""",
                "file_type": "txt",
            },
            {
                "title": "小米14 产品说明",
                "content": """小米14 产品说明

品牌：小米 (Xiaomi)
型号：小米14
发布日期：2023年10月

【核心参数】
- 芯片：骁龙8 Gen 3
- 屏幕：6.36英寸 OLED 直屏，120Hz刷新率，3000nit峰值亮度
- 存储：256GB / 512GB / 1TB
- 运行内存：8GB / 12GB / 16GB
- 后置摄像头：5000万像素光影猎人900主摄 + 5000万像素超广角 + 5000万像素长焦（3.2X光学变焦）
- 前置摄像头：3200万像素
- 电池：4610mAh，支持90W快充，50W无线快充
- 材质：金属中框，玻璃/素皮背板
- 重量：193克（玻璃版）/ 188克（素皮版）
- 系统：澎湃OS (HyperOS)
- 颜色：黑色、白色、岩石青、雪山粉

【价格】
- 8GB + 256GB：3999元
- 12GB + 256GB：4299元
- 12GB + 512GB：4599元
- 16GB + 1TB：5499元

【主要特性】
- 徕卡Summilux光学镜头
- 小米澎湃OS，全生态互联
- IP68防水防尘
- 杜比全景声双扬声器
- 红外遥控、NFC

【售后服务】
- 7天无理由退货
- 1年主机保修
- 小米客服热线：400-100-5678
- 全国小米之家及授权服务网点""",
                "file_type": "txt",
            },
            {
                "title": "MacBook Pro 14英寸 产品说明",
                "content": """MacBook Pro 14英寸 产品说明

品牌：Apple
型号：MacBook Pro 14 (M3/M3 Pro/M3 Max)
发布日期：2023年10月

【核心参数】
- 芯片：Apple M3 / M3 Pro / M3 Max
- 屏幕：14.2英寸 Liquid Retina XDR，3024x1964，120Hz ProMotion，1600nit峰值亮度
- 内存：8GB / 16GB / 18GB / 24GB / 36GB / 48GB / 64GB / 96GB / 128GB
- 存储：256GB / 512GB / 1TB / 2TB / 4TB / 8TB SSD
- 电池：70Wh，最长17小时视频播放
- 接口：3个雷雳4/USB-C、HDMI、SD卡槽、MagSafe 3、耳机孔
- 重量：1.55千克（M3版）/ 1.61千克（M3 Pro版）
- 系统：macOS Sonoma
- 颜色：深空黑色、银色

【价格】
- M3 / 8GB / 512GB：12999元
- M3 Pro / 18GB / 512GB：16999元
- M3 Pro / 18GB / 1TB：18999元
- M3 Max / 36GB / 1TB：27999元

【主要特性】
- 专业级性能：视频剪辑、3D渲染、软件开发
- 六扬声器音响系统，支持空间音频
- 1080p FaceTime HD摄像头
- 录音棚级三麦克风阵列
- 妙控键盘带Touch ID

【售后服务】
- 14天无理由退货
- 1年有限保修
- 可购买AppleCare+（3年）
- 全国Apple Store及授权服务商""",
                "file_type": "txt",
            },
            {
                "title": "平台售后政策",
                "content": """电商平台售后政策

【退换货政策】
1. 7天无理由退货
   - 商品需保持原包装完好，配件齐全
   - 不影响二次销售
   - 定制商品、鲜活易腐商品除外
   - 退款在收到退货后3-5个工作日到账

2. 15天质量问题换货
   - 商品存在非人为性能故障
   - 可选择换货或维修
   - 运费由平台承担

3. 保修服务
   - 电子产品：1年主机保修
   - 大家电：3年主要部件保修
   - 保修期内免费维修

【售后流程】
1. 进入"我的订单"，选择需要售后的商品
2. 点击"申请售后"，选择退货/换货/维修
3. 填写问题描述，上传凭证图片
4. 审核通过后，按地址寄回商品
5. 仓库验收后处理退款/换货

【运费说明】
- 质量问题：平台承担往返运费
- 7天无理由：买家承担退回运费
- 运费险：下单时可购买，理赔8-18元

【客服渠道】
- 在线客服：APP内"我的-客服中心"
- 电话客服：400-XXX-XXXX（9:00-22:00）
- 售后进度：APP内实时查询

【注意事项】
- 请保留原包装至少15天
- 激活后部分商品不支持7天无理由（如手机）
- 赠品需一并退回""",
                "file_type": "txt",
            },
        ]

        for doc_data in sample_docs:
            doc = KnowledgeDocument(
                title=doc_data["title"],
                content=doc_data["content"],
                file_type=doc_data["file_type"],
                status="indexed",
                chunk_count=0,
            )
            db.add(doc)
            db.flush()  # 获取ID

            # 简单切分（按段落）
            paragraphs = [p.strip() for p in doc_data["content"].split("\n\n") if p.strip()]
            for i, para in enumerate(paragraphs):
                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    content=para,
                    chunk_index=i,
                )
                db.add(chunk)
                doc.chunk_count += 1

        db.commit()
        print(f"[初始化] 已创建 {len(sample_docs)} 条示例知识数据")

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("  LangChain RAG 系统 - 数据初始化")
    print("=" * 50)

    # 1. 创建表
    print("\n[步骤1] 创建数据库表...")
    init_db()

    # 2. 创建管理员
    print("\n[步骤2] 创建管理员账号...")
    create_admin()

    # 3. 创建示例数据
    print("\n[步骤3] 创建示例知识数据...")
    create_sample_knowledge()

    print("\n" + "=" * 50)
    print("  初始化完成！")
    print("  管理员: admin / 123456")
    print("=" * 50)
