import os
from datetime import datetime, timezone

import discord

from models.okpan_exchange_result import OkpanExchangeResult
from models.okpan_wallet import OkpanWallet
from utils.money_util import format_money



class LogService:
    """
    운영 기록을 디스코드 로그 채널에 전송한다.
    """

    # ============================================
    # 로그 채널 조회
    # ============================================

    def _get_log_channel(
        self,
        bot: discord.Client
    ) -> discord.TextChannel | None:

        # .env에 설정된 로그 채널 ID
        channel_id = os.getenv("LOG_CHANNEL_ID")

        if not channel_id:
            print(
                ".env에 LOG_CHANNEL_ID 값이 없습니다."
            )
            return None

        try:
            channel_id_int = int(channel_id)

        except ValueError:
            print(
                "LOG_CHANNEL_ID가 올바른 숫자 형식이 아닙니다."
            )
            return None

        channel = bot.get_channel(
            channel_id_int
        )

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            print(
                "로그 채널을 찾을 수 없습니다. "
                "채널 ID와 봇 권한을 확인하세요."
            )
            return None

        return channel

    # ============================================
    # 돈 지급 로그
    # ============================================

    async def send_money_add_log(
        self,
        bot: discord.Client,
        executor: discord.abc.User,
        target: discord.abc.User,
        amount: int,
        new_balance: int,
        reason: str
    ) -> None:

        await self._send_money_log(
            bot=bot,
            executor=executor,
            target=target,
            amount=amount,
            new_balance=new_balance,
            reason=reason,
            is_add=True
        )

    # ============================================
    # 돈 차감 로그
    # ============================================

    async def send_money_remove_log(
        self,
        bot: discord.Client,
        executor: discord.abc.User,
        target: discord.abc.User,
        amount: int,
        new_balance: int,
        reason: str
    ) -> None:

        await self._send_money_log(
            bot=bot,
            executor=executor,
            target=target,
            amount=amount,
            new_balance=new_balance,
            reason=reason,
            is_add=False
        )

    # ============================================
    # 실제 돈 로그 생성
    # ============================================

    async def _send_money_log(
        self,
        bot: discord.Client,
        executor: discord.abc.User,
        target: discord.abc.User,
        amount: int,
        new_balance: int,
        reason: str,
        is_add: bool
    ) -> None:

        log_channel = self._get_log_channel(
            bot
        )

        if log_channel is None:
            return

        title = (
            "💰 지갑 지급 기록"
            if is_add
            else "💸 지갑 차감 기록"
        )

        change_amount = (
            f"+{format_money(amount)}"
            if is_add
            else f"-{format_money(amount)}"
        )

        color = (
            discord.Color.from_rgb(
                46,
                204,
                113
            )
            if is_add
            else discord.Color.from_rgb(
                231,
                76,
                60
            )
        )

        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.now(
                timezone.utc
            )
        )

        embed.add_field(
            name="처리한 운영진",
            value=(
                f"{executor.mention}\n"
                f"`{executor.name}`\n"
                f"ID: `{executor.id}`"
            ),
            inline=True
        )

        embed.add_field(
            name="처리 대상",
            value=(
                f"{target.mention}\n"
                f"`{target.name}`\n"
                f"ID: `{target.id}`"
            ),
            inline=True
        )

        embed.add_field(
            name="변동 금액",
            value=f"**{change_amount}**",
            inline=False
        )

        embed.add_field(
            name="변경 후 소지금",
            value=(
                f"**{format_money(new_balance)}**"
            ),
            inline=False
        )

        embed.add_field(
            name="사유",
            value=reason,
            inline=False
        )

        try:
            await log_channel.send(
                embed=embed
            )

            print("지갑 로그 전송 완료")

        except Exception as e:
            print(
                f"[지갑 로그 전송 실패] {e}"
            )

    # ============================================
    # 옥판 구매 로그
    # ============================================

    async def send_okpan_purchase_log(
        self,
        bot: discord.Client,
        user: discord.abc.User,
        purchased_amount: int,
        used_money: int,
        wallet_after: OkpanWallet
    ) -> None:

        log_channel = self._get_log_channel(
            bot
        )

        if log_channel is None:
            return

        embed = discord.Embed(
            title="🀄 옥판 구매 기록",
            color=discord.Color.from_rgb(
                52,
                152,
                219
            ),
            timestamp=datetime.now(
                timezone.utc
            )
        )

        embed.add_field(
            name="유저",
            value=(
                f"{user.mention}\n"
                f"`{user.name}`\n"
                f"ID: `{user.id}`"
            ),
            inline=True
        )

        embed.add_field(
            name="구매 수량",
            value=f"{purchased_amount:,}개",
            inline=True
        )

        embed.add_field(
            name="사용 금액",
            value=format_money(
                used_money
            ),
            inline=False
        )

        embed.add_field(
            name="구매 후 보유 금액",
            value=format_money(
                wallet_after.money
            ),
            inline=True
        )

        embed.add_field(
            name="구매 후 총 옥판",
            value=(
                f"{wallet_after.get_total_okpan():,}개"
            ),
            inline=True
        )

        # 돈으로 구매한 옥판은 전부 2등급
        embed.add_field(
            name="내부 처리",
            value=(
                f"2등급 옥판 "
                f"{purchased_amount:,}개 추가"
            ),
            inline=False
        )

        try:
            await log_channel.send(
                embed=embed
            )

            print("옥판 구매 로그 전송 완료")

        except Exception as e:
            print(
                f"[옥판 구매 로그 전송 실패] {e}"
            )

    # ============================================
    # 옥판 환전 로그
    # ============================================

    async def send_okpan_exchange_log(
        self,
        bot: discord.Client,
        user: discord.abc.User,
        result: OkpanExchangeResult
    ) -> None:

        log_channel = self._get_log_channel(
            bot
        )

        if log_channel is None:
            return

        wallet_after = result.wallet_after

        embed = discord.Embed(
            title="💰 옥판 환전 기록",
            color=discord.Color.from_rgb(
                241,
                196,
                15
            ),
            timestamp=datetime.now(
                timezone.utc
            )
        )

        embed.add_field(
            name="유저",
            value=(
                f"{user.mention}\n"
                f"`{user.name}`\n"
                f"ID: `{user.id}`"
            ),
            inline=True
        )

        embed.add_field(
            name="환전 수량",
            value=(
                f"{result.get_exchanged_total():,}개"
            ),
            inline=True
        )

        # 등급 정보는 운영 로그에서만 확인
        embed.add_field(
            name="내부 환전 내역",
            value=(
                f"1등급: {result.exchanged_grade1:,}개\n"
                f"2등급: {result.exchanged_grade2:,}개\n"
                f"3등급: {result.exchanged_grade3:,}개"
            ),
            inline=False
        )

        embed.add_field(
            name="지급 금액",
            value=format_money(
                result.received_money
            ),
            inline=False
        )

        embed.add_field(
            name="환전 후 보유 금액",
            value=format_money(
                wallet_after.money
            ),
            inline=True
        )

        embed.add_field(
            name="환전 후 총 옥판",
            value=(
                f"{wallet_after.get_total_okpan():,}개"
            ),
            inline=True
        )

        try:
            await log_channel.send(
                embed=embed
            )

            print("옥판 환전 로그 전송 완료")

        except Exception as e:
            print(
                f"[옥판 환전 로그 전송 실패] {e}"
            )

    # ============================================
    # 운영진 옥판 지급 로그
    # ============================================

    async def send_admin_okpan_add_log(
        self,
        bot: discord.Client,
        executor: discord.abc.User,
        target: discord.abc.User,
        grade: int,
        amount: int,
        total_okpan_after: int,
        reason: str
    ) -> None:

        log_channel = self._get_log_channel(
            bot
        )

        if log_channel is None:
            return

        embed = discord.Embed(
            title="🎁 운영진 옥판 지급 기록",
            color=discord.Color.from_rgb(
                155,
                89,
                182
            ),
            timestamp=datetime.now(
                timezone.utc
            )
        )

        embed.add_field(
            name="처리한 운영진",
            value=(
                f"{executor.mention}\n"
                f"`{executor.name}`\n"
                f"ID: `{executor.id}`"
            ),
            inline=True
        )

        embed.add_field(
            name="지급 대상",
            value=(
                f"{target.mention}\n"
                f"`{target.name}`\n"
                f"ID: `{target.id}`"
            ),
            inline=True
        )

        embed.add_field(
            name="지급 내용",
            value=(
                f"{grade}등급 옥판 "
                f"{amount:,}개"
            ),
            inline=False
        )

        embed.add_field(
            name="지급 후 총 옥판",
            value=(
                f"{total_okpan_after:,}개"
            ),
            inline=False
        )

        embed.add_field(
            name="사유",
            value=reason,
            inline=False
        )

        try:
            await log_channel.send(
                embed=embed
            )

            print("운영진 옥판 지급 로그 전송 완료")

        except Exception as e:
            print(
                f"[운영진 옥판 지급 로그 전송 실패] {e}"
            )

    # ============================================
    # 운영진 옥판 차감 로그
    # ============================================

    async def send_admin_okpan_remove_log(
        self,
        bot: discord.Client,
        executor: discord.abc.User,
        target: discord.abc.User,
        grade: int,
        amount: int,
        total_okpan_after: int,
        reason: str
    ) -> None:

        log_channel = self._get_log_channel(
            bot
        )

        if log_channel is None:
            return

        embed = discord.Embed(
            title="🀄 운영진 옥판 차감 기록",
            color=discord.Color.from_rgb(
                231,
                76,
                60
            ),
            timestamp=datetime.now(
                timezone.utc
            )
        )

        embed.add_field(
            name="처리한 운영진",
            value=(
                f"{executor.mention}\n"
                f"`{executor.name}`\n"
                f"ID: `{executor.id}`"
            ),
            inline=True
        )

        embed.add_field(
            name="차감 대상",
            value=(
                f"{target.mention}\n"
                f"`{target.name}`\n"
                f"ID: `{target.id}`"
            ),
            inline=True
        )

        # 내부 로그이므로 등급 표시
        embed.add_field(
            name="차감 내용",
            value=(
                f"{grade}등급 옥판 "
                f"{amount:,}개"
            ),
            inline=False
        )

        embed.add_field(
            name="차감 후 총 옥판",
            value=(
                f"{total_okpan_after:,}개"
            ),
            inline=False
        )

        embed.add_field(
            name="사유",
            value=reason,
            inline=False
        )

        try:
            await log_channel.send(
                embed=embed
            )

            print(
                "운영진 옥판 차감 로그 전송 완료"
            )

        except Exception as e:
            print(
                f"[운영진 옥판 차감 로그 전송 실패] {e}"
            )

    # ============================================
    # 주막 구매 로그
    # ============================================

    async def send_food_purchase_log(
        self,
        bot: discord.Client,
        user: discord.abc.User,
        cart: dict[str, int],
        food_items: dict,
        total_price: int,
        remaining_money: int
    ) -> None:

        log_channel = self._get_log_channel(
            bot
        )

        if log_channel is None:
            return

        # ========================================
        # 주문 품목 목록
        # ========================================

        item_lines = []

        for item_name, amount in cart.items():

            item = food_items[
                item_name
            ]

            price = item["price"]
            emoji = item["emoji"]

            item_total = (
                price
                * amount
            )

            item_lines.append(
                f"{emoji} **{item_name}** × {amount:,}\n"
                f"　{format_money(price)} × {amount:,}"
                f" = **{format_money(item_total)}**"
            )

        item_text = "\n\n".join(
            item_lines
        )

        if not item_text:
            item_text = (
                "주문 품목 정보 없음"
            )

        # ========================================
        # Embed
        # ========================================

        embed = discord.Embed(
            title="🍶 주막 구매 기록",
            color=discord.Color.from_rgb(
                230,
                126,
                34
            ),
            timestamp=datetime.now(
                timezone.utc
            )
        )

        embed.add_field(
            name="손님",
            value=(
                f"{user.mention}\n"
                f"`{user.name}`\n"
                f"ID: `{user.id}`"
            ),
            inline=False
        )

        embed.add_field(
            name="주문 내역",
            value=item_text,
            inline=False
        )

        embed.add_field(
            name="총 결제 금액",
            value=(
                f"**{format_money(total_price)}**"
            ),
            inline=True
        )

        embed.add_field(
            name="결제 후 소지금",
            value=(
                f"**{format_money(remaining_money)}**"
            ),
            inline=True
        )

        try:

            await log_channel.send(
                embed=embed
            )

            print(
                "주막 구매 로그 전송 완료"
            )

        except Exception as e:

            print(
                f"[주막 구매 로그 전송 실패] {e}"
            )

    # ============================================
    # 만물점 구매 로그
    # ============================================

    async def send_general_purchase_log(
        self,
        bot: discord.Client,
        user: discord.abc.User,
        cart: dict[str, int],
        general_items: dict,
        total_price: int,
        remaining_money: int
    ) -> None:

        log_channel = self._get_log_channel(
            bot
        )

        if log_channel is None:
            return

        # ========================================
        # 구매 품목 목록 생성
        # ========================================

        item_lines = []

        for item_name, amount in cart.items():

            item = general_items[
                item_name
            ]

            price = item["price"]
            emoji = item["emoji"]

            item_total = (
                price
                * amount
            )

            item_lines.append(
                f"{emoji} **{item_name}** × {amount:,}\n"
                f"　{format_money(price)} × {amount:,}"
                f" = **{format_money(item_total)}**"
            )

        item_text = "\n\n".join(
            item_lines
        )

        if not item_text:

            item_text = (
                "구매 물품 정보 없음"
            )

        # ========================================
        # Embed 생성
        # ========================================

        embed = discord.Embed(
            title="🏮 만물점 구매 기록",
            color=discord.Color.from_rgb(
                142,
                68,
                173
            ),
            timestamp=datetime.now(
                timezone.utc
            )
        )

        embed.add_field(
            name="구매 유저",
            value=(
                f"{user.mention}\n"
                f"`{user.name}`\n"
                f"ID: `{user.id}`"
            ),
            inline=False
        )

        embed.add_field(
            name="구매 내역",
            value=item_text,
            inline=False
        )

        embed.add_field(
            name="총 결제 금액",
            value=(
                f"**{format_money(total_price)}**"
            ),
            inline=True
        )

        embed.add_field(
            name="결제 후 소지금",
            value=(
                f"**{format_money(remaining_money)}**"
            ),
            inline=True
        )

        try:

            await log_channel.send(
                embed=embed
            )

            print(
                "만물점 구매 로그 전송 완료"
            )

        except Exception as e:

            print(
                f"[만물점 구매 로그 전송 실패] {e}"
            )