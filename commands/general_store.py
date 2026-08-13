import math

import discord
from discord import app_commands
from discord.ext import commands

from services.wallet_service import WalletService
from services.log_service import LogService
from utils.money_util import format_money


# ============================================
# 만물점 설정
# ============================================

ITEMS_PER_PAGE = 5


# ============================================
# 만물점 판매 품목
# ============================================
#
# 형식:
#
# "품목 이름": {
#     "price": 가격,
#     "emoji": "이모지"
# }

GENERAL_ITEMS = {
    "나무 비녀": {
        "price": 5,
        "emoji": "🌲"
    },
    "자수 손수건": {
        "price": 10,
        "emoji": "🪡"
    },
    "향낭": {
        "price": 30,
        "emoji": "👝"
    },
    "은가락지": {
        "price": 80,
        "emoji": "💍"
    },
    "은비녀": {
        "price": 100,
        "emoji": "🎀"
    },
    "산호 장식 비녀": {
        "price": 300,
        "emoji": "🪸"
    },
    "옥 가락지": {
        "price": 500,
        "emoji": "💎"
    },
    "금가락지": {
        "price": 500,
        "emoji": "👑"
    },
    "낑냥이 인형": {
        "price": 100,
        "emoji": "🐱"
    },
    "밤티 부채": {
        "price": 1,
        "emoji": "🪭"
    },
    "좋은 부채": {
        "price": 100,
        "emoji": "🪭"
    },
    "담배 한 갑": {
        "price": 5,
        "emoji": "🚬"
    },
}


class GeneralStoreCommand(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):
        self.bot = bot

        self.wallet_service = WalletService()
        self.log_service = LogService()

        self.general_carts: dict[
            int,
            dict[str, int]
        ] = {}

    # ============================================
    # /만물점
    # ============================================

    @app_commands.command(
        name="만물점",
        description="만물점에서 물품을 구매합니다."
    )
    async def 만물점(
        self,
        interaction: discord.Interaction
    ):

        user_id = interaction.user.id

        view = GeneralStoreView(
            command=self,
            user_id=user_id,
            current_page=0
        )

        await interaction.response.send_message(
            self.build_store_text(
                user_id=user_id,
                current_page=0
            ),
            view=view,
            ephemeral=True
        )

    # ============================================
    # 전체 페이지 수
    # ============================================

    def get_total_pages(
        self
    ) -> int:

        if not GENERAL_ITEMS:
            return 1

        return math.ceil(
            len(GENERAL_ITEMS)
            / ITEMS_PER_PAGE
        )

    # ============================================
    # 현재 페이지 품목
    # ============================================

    def get_page_items(
        self,
        current_page: int
    ) -> list[tuple[str, dict]]:

        items = list(
            GENERAL_ITEMS.items()
        )

        start = (
            current_page
            * ITEMS_PER_PAGE
        )

        end = (
            start
            + ITEMS_PER_PAGE
        )

        return items[
            start:end
        ]

    # ============================================
    #만물점 화면 생성
    # ============================================

    def build_store_text(
        self,
        user_id: int,
        current_page: int
    ) -> str:

        total_pages = (
            self.get_total_pages()
        )

        page_items = (
            self.get_page_items(
                current_page
            )
        )

        # ========================================
        # 판매 물품
        # ========================================

        item_lines = []

        for item_name, item in page_items:

            emoji = item["emoji"]
            price = item["price"]

            item_lines.append(
                f"{emoji} **{item_name}** - {format_money(price)}"
            )
        if item_lines:

            item_text = "\n\n".join(
                item_lines
            )

        else:

            item_text = (
                "현재 판매 중인 물품이 없습니다."
            )

        # ========================================
        # 장바구니
        # ========================================

        cart_text = (
            self.get_cart_text(
                user_id
            )
        )

        return (
            "## 🏮 만물점\n\n"
            f"**물품 목록 · {current_page + 1} / "
            f"{total_pages}**\n\n"
            f"{item_text}\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "### 🛒 장바구니\n"
            f"{cart_text}\n\n"
            "아래 메뉴에서 구매할 물품을 선택하세요."
        )

    # ============================================
    # 장바구니 추가
    # ============================================

    def add_to_cart(
        self,
        user_id: int,
        item_name: str
    ) -> None:

        cart = (
            self.general_carts.setdefault(
                user_id,
                {}
            )
        )

        cart[item_name] = (
            cart.get(
                item_name,
                0
            )
            + 1
        )

    # ============================================
    # 장바구니 비우기
    # ============================================

    def clear_cart(
        self,
        user_id: int
    ) -> None:

        self.general_carts.pop(
            user_id,
            None
        )

    # ============================================
    # 장바구니 총 금액
    # ============================================

    def get_cart_total(
        self,
        user_id: int
    ) -> int:

        cart = (
            self.general_carts.get(
                user_id,
                {}
            )
        )

        total = 0

        for item_name, amount in cart.items():

            price = (
                GENERAL_ITEMS[
                    item_name
                ]["price"]
            )

            total += (
                price
                * amount
            )

        return total

    # ============================================
    # 장바구니 표시
    # ============================================

    def get_cart_text(
        self,
        user_id: int
    ) -> str:

        cart = (
            self.general_carts.get(
                user_id,
                {}
            )
        )

        if not cart:

            return (
                "장바구니가 비어 있습니다."
            )

        lines = []

        for item_name, amount in cart.items():

            item = GENERAL_ITEMS[
                item_name
            ]

            emoji = item["emoji"]
            price = item["price"]

            item_total = (
                price
                * amount
            )

            lines.append(
                f"{emoji} **{item_name}** × {amount:,}"
                f" — {format_money(item_total)}"
            )

        total = (
            self.get_cart_total(
                user_id
            )
        )

        lines.append("")
        lines.append(
            f"**합계: {format_money(total)}**"
        )

        return "\n".join(
            lines
        )

    # ============================================
    # 결제
    # ============================================

    async def checkout(
        self,
        interaction: discord.Interaction
    ) -> None:

        user_id = (
            interaction.user.id
        )

        cart = (
            self.general_carts.get(
                user_id,
                {}
            )
        )

        # ========================================
        # 장바구니가 비어 있음
        # ========================================

        if not cart:

            await interaction.response.send_message(
                "장바구니가 비어 있습니다.",
                ephemeral=True
            )

            return

        total = (
            self.get_cart_total(
                user_id
            )
        )

        # ========================================
        # 닉네임
        # ========================================

        if isinstance(
            interaction.user,
            discord.Member
        ):

            username = (
                interaction.user.display_name
            )

        else:

            username = (
                interaction.user.name
            )

        try:

            # ====================================
            # 돈 차감
            # ====================================

            success = (
                await self.wallet_service.remove_money(
                    str(user_id),
                    username,
                    total
                )
            )

            # ====================================
            # 소지금 부족
            # ====================================

            if not success:

                current_money = (
                    await self.wallet_service.get_money(
                        str(user_id)
                    )
                )

                await interaction.response.send_message(
                    (
                        "소지금이 부족합니다.\n\n"
                        f"필요 금액: "
                        f"**{format_money(total)}**\n"
                        f"현재 소지금: "
                        f"**{format_money(current_money)}**"
                    ),
                    ephemeral=True
                )

                return

            # ====================================
            # 결제 후 잔액
            # ====================================

            new_balance = (
                await self.wallet_service.get_money(
                    str(user_id)
                )
            )

            # ====================================
            # 만물점 구매 로그
            # ====================================
            #
            # 장바구니를 비우기 전에
            # 구매한 품목을 로그에 기록한다.

            await self.log_service.send_general_purchase_log(
                bot=self.bot,
                user=interaction.user,
                cart=cart,
                general_items=GENERAL_ITEMS,
                total_price=total,
                remaining_money=new_balance
            )

            # ====================================
            # 만물점 장바구니 초기화
            # ====================================

            self.clear_cart(
                user_id
            )

            # ====================================
            # 기존 개인 만물점 화면 삭제
            # ====================================

            await interaction.response.defer()

            try:

                await interaction.delete_original_response()

            except discord.NotFound:
                pass

            # ====================================
            # 공개 결제 완료 메시지
            # ========================================
            #
            # 남은 금액이나 구매 물품은
            # 공개하지 않는다.

            await interaction.followup.send(
                (
                    "## 🏮 결제가 완료되었습니다.\n\n"
                    f"사용 금액: "
                    f"**{format_money(total)}**"
                ),
                ephemeral=False
            )

        except Exception as e:

            print(
                f"[만물점 결제 오류] {e}"
            )

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    "결제를 처리하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )

            else:

                await interaction.followup.send(
                    "결제를 처리하는 중 오류가 발생했습니다.",
                    ephemeral=True
                )


# ============================================
# 만물점 View
# ============================================

class GeneralStoreView(discord.ui.View):

    def __init__(
        self,
        command: GeneralStoreCommand,
        user_id: int,
        current_page: int
    ):

        super().__init__(
            timeout=300
        )

        self.command = command
        self.user_id = user_id
        self.current_page = current_page

        # ========================================
        # 현재 페이지 품목 선택 메뉴
        # ========================================

        self.add_item(
            GeneralSelect(
                command=command,
                user_id=user_id,
                current_page=current_page
            )
        )

        total_pages = (
            command.get_total_pages()
        )

        # 첫 페이지면 이전 버튼 비활성화
        self.previous_page.disabled = (
            current_page <= 0
        )

        # 마지막 페이지면 다음 버튼 비활성화
        self.next_page.disabled = (
            current_page
            >= total_pages - 1
        )

    # ============================================
    # 이전 페이지
    # ============================================

    @discord.ui.button(
        label="이전",
        emoji="◀️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def previous_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if self.current_page <= 0:
            return

        new_page = (
            self.current_page
            - 1
        )

        new_view = GeneralStoreView(
            command=self.command,
            user_id=self.user_id,
            current_page=new_page
        )

        await interaction.response.edit_message(
            content=self.command.build_store_text(
                user_id=self.user_id,
                current_page=new_page
            ),
            view=new_view
        )

    # ============================================
    # 다음 페이지
    # ============================================

    @discord.ui.button(
        label="다음",
        emoji="▶️",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def next_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        total_pages = (
            self.command.get_total_pages()
        )

        if (
            self.current_page
            >= total_pages - 1
        ):
            return

        new_page = (
            self.current_page
            + 1
        )

        new_view = GeneralStoreView(
            command=self.command,
            user_id=self.user_id,
            current_page=new_page
        )

        await interaction.response.edit_message(
            content=self.command.build_store_text(
                user_id=self.user_id,
                current_page=new_page
            ),
            view=new_view
        )

    # ============================================
    # 구매하기
    # ============================================

    @discord.ui.button(
        label="구매하기",
        emoji="💰",
        style=discord.ButtonStyle.success,
        row=2
    )
    async def checkout_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.command.checkout(
            interaction
        )

    # ============================================
    # 장바구니 비우기
    # ============================================

    @discord.ui.button(
        label="장바구니 비우기",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        row=2
    )
    async def clear_cart_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        self.command.clear_cart(
            self.user_id
        )

        new_view = GeneralStoreView(
            command=self.command,
            user_id=self.user_id,
            current_page=self.current_page
        )

        await interaction.response.edit_message(
            content=self.command.build_store_text(
                user_id=self.user_id,
                current_page=self.current_page
            ),
            view=new_view
        )


# ============================================
# 만물점 품목 Select
# ============================================

class GeneralSelect(discord.ui.Select):

    def __init__(
        self,
        command: GeneralStoreCommand,
        user_id: int,
        current_page: int
    ):

        self.command = command
        self.user_id = user_id
        self.current_page = current_page

        page_items = (
            command.get_page_items(
                current_page
            )
        )

        options = []

        # ========================================
        # 현재 페이지 품목만 표시
        # ========================================

        for item_name, item in page_items:

            price = item["price"]
            emoji = item["emoji"]

            options.append(
                discord.SelectOption(
                    label=item_name,
                    description=format_money(
                        price
                    ),
                    value=item_name,
                    emoji=emoji
                )
            )

        # ========================================
        # 품목이 하나도 없는 경우
        # ========================================

        if not options:

            options.append(
                discord.SelectOption(
                    label="판매 중인 물품 없음",
                    value="__EMPTY__"
                )
            )

        super().__init__(
            placeholder="구매할 물품을 선택하세요.",
            min_values=1,
            max_values=1,
            options=options,
            disabled=(
                len(page_items) == 0
            ),
            row=0
        )

    # ============================================
    # 품목 선택
    # ============================================

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        item_name = (
            self.values[0]
        )

        if item_name == "__EMPTY__":

            await interaction.response.defer()

            return

        # ========================================
        # 만물점 장바구니 +1
        # ========================================

        self.command.add_to_cart(
            self.user_id,
            item_name
        )

        new_view = GeneralStoreView(
            command=self.command,
            user_id=self.user_id,
            current_page=self.current_page
        )

        # 새 메시지를 만들지 않고
        # 기존 만물점 화면만 갱신
        await interaction.response.edit_message(
            content=self.command.build_store_text(
                user_id=self.user_id,
                current_page=self.current_page
            ),
            view=new_view
        )