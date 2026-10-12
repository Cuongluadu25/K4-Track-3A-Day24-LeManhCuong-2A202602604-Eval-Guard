"""NeMo Guardrails custom LLM provider — cho mọi backend OpenAI-compatible.

Vì sao cần file này
-------------------
NeMo Guardrails 0.10.0 chỉ trả về `ChatOpenAI` khi tên model chứa `gpt-3.5`
hoặc `gpt-4` (nemoguardrails/llm/providers/providers.py:217-221). Nếu không,
nó rơi xuống nhánh cuối (providers.py:278) và trả về `langchain_openai.OpenAI`
— class gọi **Completions API cũ**, không dùng được với các model chat-only
như `deepseek-chat`.

Cách xử lý
----------
`engine` trong `guardrails/config.yml` được khai là `compat`. Vì tên engine
này khác `"openai"`, điều kiện ở providers.py:218 không được thoả và NeMo
dùng thẳng class đã đăng ký bên dưới (providers.py:278). Không sửa gì vào
package đã cài, không sửa scaffold `src/phase_c_guard.py:91`.

Nhờ vậy `base_url` do `ChatOpenAI` tự đọc từ biến môi trường `OPENAI_API_BASE`
(langchain_openai/chat_models/base.py:489-490), nên đổi nhà cung cấp chỉ cần
sửa `.env`, không phải sửa code.

Lưu ý quan trọng
----------------
`model:` trong `guardrails/config.yml` phải khớp với model thật ở đây, vì
`src/experiment_support.py:guard_models()` đọc `rails.config.models[i].model`
và ghi thẳng giá trị đó vào metadata của `artifacts/guard_results.json`.
Khai một đằng chạy một nẻo là ghi sai kết quả thật, vi phạm doc/RULES.md.
"""
from __future__ import annotations

import os

from langchain_core.pydantic_v1 import Field
from langchain_openai import ChatOpenAI
from nemoguardrails.llm.providers import register_llm_provider

# Model thật sẽ gọi. GIÁ TRỊ DEFAULT PHẢI TRÙNG `model:` trong config.yml.
#
# Vì sao phải trùng: NeMo không truyền `model` xuống engine tự đăng ký — điều
# kiện là `"model" in provider_cls.__fields__` (llmrails.py:356-359), mà field
# của ChatOpenAI tên `model_name` (alias `model`), nên điều kiện đó False. Model
# thật do đó lấy từ biến môi trường ở đây. Trong khi đó
# `src/experiment_support.py:guard_models()` lại đọc `model:` từ config.yml và
# ghi thẳng vào metadata kết quả. Hai nguồn lệch nhau = ghi sai kết quả thật,
# vi phạm doc/RULES.md.
#
# `scripts/check_lab.py` KHÔNG kiểm tra sự lệch này, nên tự đối chiếu khi đổi
# nhà cung cấp:
#     python -c "import yaml,guardrails.config as c; \
#       print(c.DEFAULT_MODEL, yaml.safe_load(open('guardrails/config.yml'))['models'][0]['model'])"
# Hai giá trị in ra phải giống nhau.
DEFAULT_MODEL = os.getenv("LAB_LLM_MODEL", "deepseek-flash")

# Tên engine dùng trong guardrails/config.yml.
ENGINE_NAME = "compat"


class CompatChatOpenAI(ChatOpenAI):
    """`ChatOpenAI` trỏ vào endpoint OpenAI-compatible bất kỳ.

    NeMo KHÔNG truyền `model` xuống cho engine tự đăng ký: nó chỉ làm việc đó
    khi `"model" in provider_cls.__fields__` (llmrails.py:356-359), mà field
    của `ChatOpenAI` tên là `model_name` (alias `model`) — kiểm chứng bằng
    `ChatOpenAI.__fields__`. Nên model phải được khai làm default ngay tại đây.
    """

    model_name: str = Field(default=DEFAULT_MODEL, alias="model")

    # `reasoning_effort: none` (tắt phần suy luận của model reasoning) KHÔNG khai
    # ở đây được: `build_extra` của langchain_openai dựng lại `model_kwargs` từ
    # tham số constructor (chat_models/base.py:466-467), nên default khai bằng
    # Field sẽ bị reset về {}. Khai trong `parameters:` của guardrails/config.yml
    # — NeMo truyền thẳng nó vào constructor (llmrails.py:335).


register_llm_provider(ENGINE_NAME, CompatChatOpenAI)
