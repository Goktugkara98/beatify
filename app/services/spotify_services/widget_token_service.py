# =============================================================================
# Widget Token Servis Modülü (Widget Token Service Module)
# =============================================================================
# Bu modül, uygulama içi widget'lar (örn: Spotify "Şu An Çalan" widget'ı)
# için güvenli token'lar oluşturma, doğrulama ve bu token'lardan bilgi
# (kullanıcı adı, widget yapılandırması) çıkarma işlemlerini yöneten bir
# servis sınıfı (WidgetTokenService) içerir. Token'lar, kullanıcıya özel
# widget erişimini ve yapılandırmasını güvenli bir şekilde sağlamak için kullanılır.
#
# İÇİNDEKİLER:
# -----------------------------------------------------------------------------
# 1.0  İÇE AKTARMALAR (IMPORTS)
#      : Gerekli Python modüllerinin (secrets, base64, json, time, datetime)
#        içe aktarılması.
# 2.0  WIDGET TOKEN SERVİS SINIFI (WIDGET TOKEN SERVICE CLASS)
#      2.1. WidgetTokenService
#           : Widget token işlemlerini yöneten ana servis sınıfı.
#           2.1.1.  __init__()
#                   : Başlatıcı metot. Token geçerlilik süresini ayarlar.
#           2.1.2.  generate_widget_token(username, widget_config)
#                   : Belirtilen kullanıcı ve widget yapılandırması için güvenli bir widget token'ı oluşturur.
#           2.1.3.  validate_widget_token(token)
#                   : Verilen widget token'ının geçerliliğini (süre sonu vb.) kontrol eder ve payload'u çıkarır.
#           2.1.4.  get_widget_config_from_token(token)
#                   : Geçerli bir widget token'ından widget yapılandırma bilgilerini çıkarır.
#           2.1.5.  get_username_from_token(token)
#                   : Geçerli bir widget token'ından kullanıcı adını çıkarır.
# =============================================================================

# =============================================================================
# 1.0 İÇE AKTARMALAR (IMPORTS)
# =============================================================================
import secrets      # Güvenli rastgele sayılar ve token'lar üretmek için
import base64       # Base64 encode/decode işlemleri için
import json         # JSON verilerini serialize/deserialize etmek için
import time         # Zaman damgaları için (Unix timestamp)
from datetime import datetime, timedelta # Tarih ve zaman işlemleri, süreler için
from typing import Dict, Any, Optional, Tuple # Tip ipuçları için

# =============================================================================
# 2.0 WIDGET TOKEN SERVİS SINIFI (WIDGET TOKEN SERVICE CLASS)
# =============================================================================
class WidgetTokenService:
    """
    Widget'lar için güvenli erişim token'ları oluşturma, doğrulama ve
    bu token'lardan bilgi çıkarma işlemlerini yönetir.
    """

    # -------------------------------------------------------------------------
    # 2.1.1. __init__() : Başlatıcı metot.
    # -------------------------------------------------------------------------
    def __init__(self, token_validity_days: int = 30):
        """
        WidgetTokenService sınıfının başlatıcı metodu.

        Args:
            token_validity_days (int, optional): Oluşturulan widget token'larının
                                                 kaç gün geçerli olacağını belirtir.
                                                 Varsayılan değer 30 gündür.
        """
        self.token_validity_days: int = token_validity_days
        # print(f"WidgetTokenService örneği oluşturuldu. Token geçerlilik süresi: {self.token_validity_days} gün.") # Geliştirme için log

    # -------------------------------------------------------------------------
    # 2.1.2. generate_widget_token(...) : Güvenli bir widget token'ı oluşturur.
    # -------------------------------------------------------------------------
    def generate_widget_token(self, username: str, widget_config: Dict[str, Any]) -> str:
        """
        Belirtilen kullanıcı adı ve widget yapılandırması için güvenli,
        süre limitli bir widget erişim token'ı oluşturur.
        Token içeriği JSON formatında olup Base64 ile encode edilir.

        Args:
            username (str): Token'ın ilişkilendirileceği kullanıcının adı.
            widget_config (Dict[str, Any]): Widget'a özel yapılandırma bilgilerini
                                            içeren sözlük. Örneğin:
                                            {
                                                'type': 'spotify-nowplaying', // Widget türü
                                                'theme': 'dark',              // Widget teması
                                                'show_album_art': True       // Albüm kapağını göster
                                            }

        Returns:
            str: Oluşturulan Base64 URL-safe encode edilmiş widget token'ı.
        """
        # print(f"Widget token oluşturuluyor: Kullanıcı={username}, Config={widget_config}") # Geliştirme için log
        try:
            if not username or not isinstance(widget_config, dict):
                raise ValueError("Kullanıcı adı ve widget yapılandırması gereklidir ve yapılandırma bir sözlük olmalıdır.")

            current_timestamp: int = int(time.time())
            expires_at_timestamp: int = int((datetime.now() + timedelta(days=self.token_validity_days)).timestamp())

            payload: Dict[str, Any] = {
                'username': username,
                'iat': current_timestamp,          # Issued at - Oluşturulma zamanı
                'exp': expires_at_timestamp,       # Expiration time - Son geçerlilik zamanı
                'widget_config': widget_config,    # Widget'a özel yapılandırma
                'nonce': secrets.token_hex(16)     # Tekrarlanan token üretimini engellemek ve güvenliği artırmak için rastgele değer
            }

            serialized_payload: str = json.dumps(payload, sort_keys=True) # Anahtarları sıralayarak tutarlı çıktı
            encoded_token: str = base64.urlsafe_b64encode(serialized_payload.encode('utf-8')).decode('utf-8')
            
            # print(f"Oluşturulan widget token: {encoded_token[:20]}...") # Geliştirme için log
            return encoded_token
        except Exception as e:
            # print(f"Widget token oluşturulurken hata: {str(e)}") # Geliştirme için log
            # Hata durumunda boş bir token veya özel bir hata token'ı döndürmek yerine
            # istisnayı yukarı fırlatmak daha iyi olabilir, çağıran tarafın haberi olur.
            raise RuntimeError(f"Widget token oluşturulamadı: {str(e)}") from e

    # -------------------------------------------------------------------------
    # 2.1.3. validate_widget_token(...) : Widget token'ını doğrular ve payload'u çıkarır.
    # -------------------------------------------------------------------------
    def validate_widget_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verilen widget token'ının geçerliliğini kontrol eder (decode etme,
        JSON parse etme, son kullanma tarihi kontrolü).

        Args:
            token (str): Doğrulanacak Base64 URL-safe encode edilmiş widget token'ı.

        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]:
                - İlk eleman (bool): Token geçerliyse True, değilse False.
                - İkinci eleman (Optional[Dict[str, Any]]): Token geçerliyse
                  decode edilmiş payload (sözlük), değilse None.
        """
        # print(f"Widget token doğrulanıyor: {token[:20]}...") # Geliştirme için log
        if not token or not isinstance(token, str):
            # print("Doğrulama için geçersiz token formatı veya boş token.") # Geliştirme için log
            return False, None
        try:
            # Base64 decode etme (padding hatalarını da yakalamak için try-except içinde)
            try:
                decoded_payload_bytes: bytes = base64.urlsafe_b64decode(token.encode('utf-8'))
            except base64.binascii.Error as b64_error: # type: ignore[attr-defined]
                # print(f"Base64 decode hatası: {str(b64_error)}") # Geliştirme için log
                return False, None
                
            decoded_payload_str: str = decoded_payload_bytes.decode('utf-8')
            
            # JSON parse etme
            payload: Dict[str, Any] = json.loads(decoded_payload_str)

            # Gerekli alanların varlığını kontrol et (isteğe bağlı ama iyi bir pratik)
            required_fields = ['username', 'iat', 'exp', 'widget_config', 'nonce']
            if not all(field in payload for field in required_fields):
                # print(f"Token payload'unda eksik alanlar var. Mevcut alanlar: {payload.keys()}") # Geliştirme için log
                return False, None

            # Son kullanma tarihini kontrol et
            current_timestamp: int = int(time.time())
            if current_timestamp > payload.get('exp', 0):
                # print(f"Token süresi dolmuş. Bitiş: {payload.get('exp')}, Şu an: {current_timestamp}") # Geliştirme için log
                return False, None # Token süresi dolmuş

            # print(f"Widget token geçerli. Payload: {payload}") # Geliştirme için log
            return True, payload
        except json.JSONDecodeError as json_err:
            # print(f"Token payload JSON decode hatası: {str(json_err)}") # Geliştirme için log
            return False, None
        except UnicodeDecodeError as uni_err:
            # print(f"Token payload UTF-8 decode hatası: {str(uni_err)}") # Geliştirme için log
            return False, None
        except Exception as e: # Diğer beklenmedik hatalar
            # Orijinal kodda print vardı, bu iyi bir loglama noktası.
            print(f"Widget token doğrulanırken genel bir hata oluştu: {str(e)}") # Hata loglama
            # import traceback
            # print(traceback.format_exc()) # Detaylı hata için
            return False, None

    # -------------------------------------------------------------------------
    # 2.1.4. get_widget_config_from_token(...) : Token'dan widget yapılandırmasını çıkarır.
    # -------------------------------------------------------------------------
    def get_widget_config_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Geçerli bir widget token'ından widget'a özel yapılandırma bilgilerini çıkarır.

        Args:
            token (str): Bilgilerin çıkarılacağı widget token'ı.

        Returns:
            Optional[Dict[str, Any]]: Token geçerliyse widget yapılandırma sözlüğü,
                                      değilse None.
        """
        # print(f"Token'dan widget yapılandırması alınıyor: {token[:20]}...") # Geliştirme için log
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            # print("Token geçersiz, yapılandırma alınamadı.") # Geliştirme için log
            return None
        
        widget_config = payload.get('widget_config')
        # if widget_config:
            # print(f"Widget yapılandırması başarıyla alındı: {widget_config}") # Geliştirme için log
        # else:
            # print("Token payload'unda widget yapılandırması bulunamadı.") # Geliştirme için log
        return widget_config

    # -------------------------------------------------------------------------
    # 2.1.5. get_username_from_token(...) : Token'dan kullanıcı adını çıkarır.
    # -------------------------------------------------------------------------
    def get_username_from_token(self, token: str) -> Optional[str]:
        """
        Geçerli bir widget token'ından token'ın sahibi olan kullanıcının adını çıkarır.

        Args:
            token (str): Kullanıcı adının çıkarılacağı widget token'ı.

        Returns:
            Optional[str]: Token geçerliyse kullanıcı adı, değilse None.
        """
        # print(f"Token'dan kullanıcı adı alınıyor: {token[:20]}...") # Geliştirme için log
        is_valid, payload = self.validate_widget_token(token)
        if not is_valid or not payload:
            # print("Token geçersiz, kullanıcı adı alınamadı.") # Geliştirme için log
            return None
            
        username = payload.get('username')
        # if username:
            # print(f"Kullanıcı adı başarıyla alındı: {username}") # Geliştirme için log
        # else:
            # print("Token payload'unda kullanıcı adı bulunamadı.") # Geliştirme için log
        return username

# =============================================================================
# Widget Token Servis Modülü Sonu
# =============================================================================
