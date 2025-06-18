from typing import Optional, List
from pydantic import Field, PrivateAttr, ConfigDict
from langchain_core.language_models import LLM
from llama_cpp import Llama


class TinyLlamaLLM(LLM):
    # --- campos configurables (públicos) ---
    model_path: str = Field(
        default="./TinyLlama-1.1B-Chat-v1.0-GGUF/tinyllama-1.1b-chat-v1.0.Q8_0.gguf"
    )
    n_ctx: int = Field(default=2048)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=256)

    # --- atributo privado donde guardaremos la instancia real de llama_cpp.Llama ---
    _model: Llama = PrivateAttr()

    # --- configuración Pydantic: permitir tipos arbitrarios ---
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ----------------------------------------------------------
    def __init__(self, **kwargs):
        super().__init__(**kwargs)          # inicializa BaseModel
        # ahora sí podemos asignar el atributo privado
        self._model = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=4,
            f16_kv=True,
            use_mlock=True,
        )
        print("✅ TinyLlama cargado y listo")

    # ----------------------------------------------------------
    @property
    def _llm_type(self) -> str:             # requerido por LangChain
        return "tinyllama_local"

    # ----------------------------------------------------------
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Método que LangChain invoca internamente para obtener una respuesta del modelo."""
        out = self._model(
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop=stop,
        )

        # LangChain espera un string como salida
        return out["choices"][0]["text"].strip()