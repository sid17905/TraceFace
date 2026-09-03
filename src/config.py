from pydantic_settings import BaseSettings, SettingsConfigDict


class TraceFaceSettings(BaseSettings):
    # Member 1: AI / CV Configuration
    face_detection_confidence: float = 0.85
    face_similarity_threshold: float = -1.0
    embedding_model_backbone: str = "buffalo_l"
    device: str = "cpu"

    # Member 2: OSINT & Web Search API Keys
    serpapi_key: str = ""
    bing_visual_search_key: str = ""
    playwright_headless: bool = True
    search_max_candidates: int = 10

    # Member 3: Web3 & Storage Configuration
    rpc_url: str = "http://127.0.0.1:8545"
    chain_id: int = 31337
    private_key: str = ""
    contract_address: str = ""
    pinata_api_key: str = ""
    pinata_secret_key: str = ""
    ipfs_gateway: str = "https://gateway.pinata.cloud/ipfs/"

    # Global CLI Settings
    log_level: str = "INFO"
    enable_rich_terminal: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = TraceFaceSettings()
