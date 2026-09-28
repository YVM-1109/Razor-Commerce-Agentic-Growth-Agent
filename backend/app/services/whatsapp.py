class MockWhatsApp:
    def send_notification(self, phone: str, message: str) -> bool:
        return bool(phone)
whatsapp_client=MockWhatsApp()
