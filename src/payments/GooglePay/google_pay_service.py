import os
from typing import Dict, Any


class GooglePayService:
    """Service xử lý thanh toán Google Pay"""

    def get_google_pay_config(self) -> Dict[str, Any]:
        """
        Lấy Google Pay configuration

        Returns:
            Dict chứa Google Pay config
        """
        try:
            merchant_id = os.getenv('GOOGLE_PAY_MERCHANT_ID', '')
            merchant_name = os.getenv('GOOGLE_PAY_MERCHANT_NAME', 'High5 Gen Book')
            gateway_name = os.getenv('GOOGLE_PAY_GATEWAY', 'example')
            environment = os.getenv('GOOGLE_PAY_ENVIRONMENT', 'TEST')

            if not merchant_id:
                return {
                    "success": False,
                    "message": "Google Pay merchant ID not configured"
                }

            return {
                "success": True,
                "environment": environment,  # TEST or PRODUCTION
                "apiVersion": 2,
                "apiVersionMinor": 0,
                "merchantInfo": {
                    "merchantId": merchant_id,
                    "merchantName": merchant_name
                },
                "allowedPaymentMethods": [{
                    "type": "CARD",
                    "parameters": {
                        "allowedAuthMethods": ["PAN_ONLY", "CRYPTOGRAM_3DS"],
                        "allowedCardNetworks": ["MASTERCARD", "VISA"]
                    },
                    "tokenizationSpecification": {
                        "type": "PAYMENT_GATEWAY",
                        "parameters": {
                            "gateway": gateway_name,
                            "gatewayMerchantId": merchant_id
                        }
                    }
                }],
                "transactionInfo": {
                    "totalPriceStatus": "FINAL",
                    "totalPrice": "11.99",
                    "currencyCode": "USD",
                    "countryCode": "US"
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get Google Pay configuration"
            }

    def process_google_pay_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý payment data từ Google Pay

        Args:
            payment_data: Payment data từ Google Pay

        Returns:
            Dict chứa kết quả xử lý payment
        """
        try:
            # Trong thực tế, sẽ gửi payment data đến payment processor
            # Ở đây chỉ simulate success
            token = payment_data.get('paymentMethodData', {}).get('tokenizationData', {}).get('token')

            if not token:
                return {
                    "success": False,
                    "message": "Invalid payment token"
                }

            # Simulate payment processing
            return {
                "success": True,
                "transaction_id": f"gpay_{payment_data.get('apiVersion', '2')}_{hash(str(payment_data))}",
                "amount": 11.99,
                "currency": "USD",
                "status": "completed"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process Google Pay payment"
            }


# Singleton instance
google_pay_service = GooglePayService()
