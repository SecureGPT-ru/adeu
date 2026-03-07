from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, PrivateAttr

from adeu.redline.mapper import DocumentMapper


class EditOperationType:
    """Internal enum for low-level XML manipulation"""

    INSERTION = "INSERTION"
    DELETION = "DELETION"
    MODIFICATION = "MODIFICATION"


class DocumentEdit(BaseModel):
    """
    Represents a single atomic edit suggested by the LLM.
    The engine treats this as a "Search and Replace" operation.
    """

    target_text: str = Field(
        ...,
        description=(
            "Exact text to find. If the text appears multiple times (e.g. 'Fee'), include surrounding context. "
            "You can include CriticMarkup {==...==} in the target to match text inside existing markup."
        ),
    )

    new_text: str = Field(
        ...,
        description=(
            "The desired text replacement. You may use Markdown formatting: "
            "'# Title' for headers, '**bold**' for bold, '_italic_' for italic. "
            "Do NOT try to manually write {++...++} tags; the engine handles tracking."
        ),
    )

    comment: Optional[str] = Field(
        None,
        description="Text to appear in a comment bubble (Review Pane) linked to this edit.",
    )

    # Internal use only. PrivateAttr is invisible to the MCP API schema.
    _match_start_index: Optional[int] = PrivateAttr(default=None)
    _internal_op: Optional[str] = PrivateAttr(default=None)
    _active_mapper_ref: Optional[DocumentMapper] = PrivateAttr(default=None)


class EditStatus(str, Enum):
    """Статус применения одной правки."""
    APPLIED = "applied"
    SKIPPED_NOT_FOUND = "skipped_not_found"
    SKIPPED_OVERLAP = "skipped_overlap"


class EditResult(BaseModel):
    """
    Результат применения одной правки.
    Содержит детальную информацию о том, что произошло при применении.
    """

    # Входные данные (что просили)
    target_text: str = Field(..., description="Исходный target_text из DocumentEdit")
    new_text: str = Field(..., description="Исходный new_text из DocumentEdit")
    comment: Optional[str] = Field(None, description="Комментарий к правке (если был)")

    # Результат
    status: EditStatus = Field(..., description="Статус: applied, skipped_not_found, skipped_overlap")

    # Детали (только если status == APPLIED)
    matched_text: Optional[str] = Field(
        None,
        description="Текст, который реально был найден (может отличаться из-за fuzzy matching)"
    )
    context_with_markup: Optional[str] = Field(
        None,
        description="Фрагмент документа с CriticMarkup: ~80 символов до + {--old--}{++new++} + ~80 символов после"
    )


class ReviewActionType(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REPLY = "REPLY"


class ReviewAction(BaseModel):
    """
    Meta-actions on existing markup (Track Changes / Comments).
    Used for negotiation and approval workflows.
    """

    action: ReviewActionType = Field(..., description="ACCEPT, REJECT, or REPLY.")
    target_id: str = Field(..., description="The full ID string from the document text (e.g. 'Chg:1' or 'Com:5').")

    text: Optional[str] = Field(None, description="For REPLY: The content of the reply body.")
    comment: Optional[str] = Field(None, description="For ACCEPT/REJECT: Optional rationale.")
