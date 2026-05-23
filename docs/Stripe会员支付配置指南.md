# Stripe 会员支付配置指南

本文说明如何在本地（无需公网 IP）完成 **Stripe 测试模式 + 一次性买断 VIP（CNY）** 的配置与联调。

## 一、你需要准备什么

| 项目 | 说明 |
|------|------|
| Stripe 账号 | [注册 Test mode](https://dashboard.stripe.com/register)（需能访问 Stripe，国内通常需代理） |
| Stripe CLI | [下载 Windows 版](https://github.com/stripe/stripe-cli/releases) |
| 后端 `.env` | 复制 `backend/.env.example` 为 `backend/.env` 并填写密钥 |

## 二、在 Stripe Dashboard 创建商品（人民币 · 一次性）

1. 确保右上角处于 **Test mode（测试模式）**
2. 进入 **Product catalog → Add product**
3. 填写：
   - Name：`SaveAny VIP 永久版`
   - **Pricing model：One time（一次性）**
   - **Price：CNY ¥29**（金额需与前端展示一致）
4. 保存后复制 **Price ID**（形如 `price_1ABC...`）
5. 填入 `backend/.env`：

```env
STRIPE_PRICE_ID=price_xxxxxxxx
```

## 三、获取 API 密钥

Dashboard → **Developers → API keys**（Test mode）：

```env
STRIPE_SECRET_KEY=sk_test_xxxxxxxx
```

> 切勿将 `sk_test_` / `sk_live_` 提交到 Git 或放到前端代码中。

## 四、本地 Webhook（无外网也能测）

Stripe 无法直接访问你本机的 `localhost`，因此用 **Stripe CLI** 建立 WebSocket 隧道转发事件：

```powershell
# 1. 登录（只需做一次）
stripe login

# 2. 启动转发（保持此窗口运行）
stripe listen --forward-to localhost:8000/api/stripe/webhook
```

终端会输出：

```text
Ready! Your webhook signing secret is whsec_xxxxxxxx
```

将其填入：

```env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxx
```

## 五、启动项目

```powershell
# 终端 1：后端
cd backend
pip install -r requirements.txt
# 确保 .env 已配置 JWT_SECRET、STRIPE_* 等
uvicorn main:app --reload --port 8000

# 终端 2：Stripe CLI（见上一节）

# 终端 3：前端
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

## 六、完整测试流程

1. **注册账号**：导航栏 → 登录 → 注册
2. **购买 VIP**：套餐区 → 「立即购买 VIP」
3. 跳转到 Stripe 测试收银台，填写：
   - 卡号：`4242 4242 4242 4242`
   - 有效期：任意未来日期（如 `12/34`）
   - CVC：任意 3 位（如 `123`）
4. 支付成功后回跳到首页，应看到「VIP 已开通」
5. 在 `stripe listen` 终端确认收到 `checkout.session.completed`
6. 尝试下载超过 3 次：免费用户会收到 429；VIP 无限制

### 不打开浏览器的快速触发（可选）

```powershell
stripe trigger checkout.session.completed
```

> 注意：`trigger` 生成的是通用测试事件，**不会自动关联你的 user_id**。完整联调仍建议走真实 Checkout 流程。

## 七、安全与幂等（已实现）

| 机制 | 实现 |
|------|------|
| VIP 开通来源 | Webhook `checkout.session.completed` 验签通过后写入数据库；支付回跳 `/api/billing/verify` 可兜底同步 |
| VIP 撤销 | Webhook `charge.refunded` / `refund.created`；`/api/auth/me` 会主动与 Stripe 同步退款状态 |
| 幂等 | `processed_stripe_events` 表以 `event.id` 去重 |
| 创建 Checkout 幂等 | Stripe API `idempotency_key=checkout-user-{user_id}` |
| 下载限流 | 免费用户每日 3 次（UTC 日切），VIP 不限 |
| 格式权限 | 免费用户最高 720p；1080p+ 与仅音频格式后端强制校验 |
| AI 功能 | `/api/summarize*`、`/api/chat` 仅 VIP 可调用 |
| 密钥 | 仅存在于 `backend/.env` |

## 八、上线 checklist

1. Stripe Dashboard 切换到 **Live mode**，重新创建 CNY 一次性 Price
2. 更新生产 `.env`：
   - `STRIPE_SECRET_KEY=sk_live_...`
   - `STRIPE_PRICE_ID=price_live_...`
   - `STRIPE_WEBHOOK_SECRET=whsec_...`（Dashboard → Webhooks 添加 `https://你的域名/api/stripe/webhook`）
   - `FRONTEND_ORIGIN=https://你的域名`
   - `JWT_SECRET=` 足够长的随机字符串
3. 前端构建并部署，`VITE_SITE_ORIGIN` 设为正式域名
4. 用 Live 模式小额真实支付验证一次完整流程

## 九、常见问题

**Q：完全断网能测吗？**  
不能。Stripe API 与 CLI 均需联网。Webhook 接收不需要公网 IP，CLI 会转发到本地。

**Q：支付成功但 VIP 未开通？**  
检查 `stripe listen` 是否在运行、`STRIPE_WEBHOOK_SECRET` 是否与 CLI 输出一致、后端日志是否有 webhook 错误。

**Q：CNY 测试模式收不到人民币选项？**  
创建 Product 时 Currency 选 **CNY**；若账户地区限制，可先用 USD 测试流程，上线前再换 CNY Price ID。

**Q：重复点击购买会扣两次吗？**  
同一用户创建 Checkout 使用了 idempotency_key；已是 VIP 的用户后端会拒绝再次创建会话。

**Q：Stripe 退款后仍是 VIP？**  
确认 Webhook 已收到 `charge.refunded`，或刷新页面触发 `/api/auth/me`（会自动同步 Stripe 退款状态）。退款后需**重新解析**视频以刷新格式列表。

**Q：成为 VIP 后仍只显示 480p？**  
通常是 YouTube Cookie 失效，与会员状态无关。请重新导出 `backend/cookies.txt` 并重启后端，然后**重新粘贴链接解析**（不要沿用旧结果）。

**Q：免费用户能看到 1080p 吗？**  
列表中会显示带 **VIP** 标记的 1080p/4K 选项（灰色锁定），点击可引导升级；实际下载最高 720p。
