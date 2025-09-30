# Payment Methods Sandbox Setup Guide

## 🏆 Apple Pay Sandbox

### 1. Apple Developer Account
- Truy cập: https://developer.apple.com/
- Tạo Apple Pay Merchant ID và Certificate
- Download Merchant Identity Certificate (cho sandbox)

### 2. Environment Variables
```bash
APPLE_PAY_MERCHANT_ID=merchant.com.yourdomain.app
APPLE_PAY_MERCHANT_DOMAIN=localhost:3000
APPLE_PAY_CERTIFICATE_PATH=/path/to/merchant_id.pem
APPLE_PAY_SANDBOX=true  # true = sandbox, false = production
```

### 3. Test Cards
Apple Pay sử dụng real payment methods. Test bằng:
- iPhone/iPad với Safari
- Apple Watch
- Real credit/debit cards

## 🎯 Google Pay Sandbox

### 1. Google Pay Business Console
- Truy cập: https://pay.google.com/business/console
- Tạo Business Profile
- Get Merchant ID và Gateway credentials

### 2. Environment Variables
```bash
GOOGLE_PAY_MERCHANT_ID=BCR2DN4TXXXXXXXXX  # Real merchant ID
GOOGLE_PAY_MERCHANT_NAME=High5 Gen Book
GOOGLE_PAY_GATEWAY=stripe  # or your payment processor
GOOGLE_PAY_ENVIRONMENT=TEST  # TEST or PRODUCTION
```

### 3. Test Cards
```
Visa: 4111 1111 1111 1111
Mastercard: 5555 5555 5555 4444
```

## 📦 Amazon Pay Sandbox

### 1. Amazon Seller Central
- Truy cập: https://sellercentral.amazon.com/
- Đăng ký Amazon Pay
- Get Merchant ID, Store ID, Public Key ID

### 2. Environment Variables
```bash
AMAZON_PAY_MERCHANT_ID=ABCDEF...  # Real merchant ID
AMAZON_PAY_PUBLIC_KEY_ID=ABCD1234...  # Public key ID
AMAZON_PAY_STORE_ID=amzn1.application-oa2-client.1234567890abcdef
AMAZON_PAY_REGION=US
AMAZON_PAY_SANDBOX=true  # true = sandbox, false = production
```

### 3. Test Accounts
- Sử dụng Amazon test accounts trong sandbox
- Test với virtual payment methods

## 🧪 Test Flow

### Apple Pay
```javascript
// Sandbox mode tự động detect
const session = new ApplePaySession(1, paymentRequest);
// Sẽ connect đến Apple Pay sandbox servers
```

### Google Pay
```javascript
const paymentsClient = new google.payments.api.PaymentsClient({
    environment: 'TEST'  // ← Sandbox mode
});
```

### Amazon Pay
```javascript
amazon.Pay.renderButton('#container', {
    sandbox: true,  // ← Sandbox mode
    // ... other config
});
```

## 🔒 Production Setup

Khi chuyển sang production:

1. **Apple Pay**: Upload production certificate
2. **Google Pay**: Change `GOOGLE_PAY_ENVIRONMENT=PRODUCTION`
3. **Amazon Pay**: Set `AMAZON_PAY_SANDBOX=false`

## ⚠️ Important Notes

- **Apple Pay**: Chỉ hoạt động trên Safari và Apple devices
- **Google Pay**: Hoạt động trên tất cả browsers
- **Amazon Pay**: Cần Amazon account để test
- **PayPal**: Đã có sandbox mode hoạt động

## 🚀 Quick Test

1. Set tất cả environment variables thành sandbox values
2. Restart Docker: `docker-compose restart`
3. Test từng payment method trên checkout page
4. Use test cards cho Google Pay
5. Use real Apple Pay/Google Pay accounts cho Apple Pay/Google Pay
