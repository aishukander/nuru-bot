import discord
from discord.ext import commands
import re
from collections import defaultdict
import random
from datetime import datetime, timedelta, timezone

class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Helper function to parse duration string
    @staticmethod
    def parse_duration(duration_str: str) -> float | None:
        if not duration_str:
            return None
        total_seconds = 0
        # Regex to find digits followed by s, m, h, or d (case-insensitive)
        matches = re.findall(r'(\d+)\s*(s|m|h|d)', duration_str, re.IGNORECASE)
        if not matches:
            return None # Return None if format is invalid

        for value, unit in matches:
            try:
                value = int(value)
                if unit.lower() == 's':
                    total_seconds += value
                elif unit.lower() == 'm':
                    total_seconds += value * 60
                elif unit.lower() == 'h':
                    total_seconds += value * 60 * 60
                elif unit.lower() == 'd':
                    total_seconds += value * 24 * 60 * 60
            except ValueError:
                return None # Invalid number format

        # discord has a max duration of 4 weeks (4 * 7 days)
        max_duration = 4 * 7 * 24 * 60 * 60
        return min(total_seconds, max_duration) if total_seconds > 0 else None

    # Helper function to parse allowed roles/users string
    @staticmethod
    def parse_allowed(allowed_str: str, guild: discord.Guild) -> tuple[set[int], set[int]]:
        allowed_roles = set()
        allowed_users = set()
        if allowed_str and guild:
            parts = allowed_str.split()
            for part in parts:
                role_match = re.match(r'<@&(\d+)>', part)
                user_match = re.match(r'<@!?(\d+)>', part)
                if role_match:
                    role_id = int(role_match.group(1))
                    if guild.get_role(role_id):
                        allowed_roles.add(role_id)
                elif user_match:
                    user_id = int(user_match.group(1))
                    if guild.get_member(user_id): # Check if user is in the guild
                        allowed_users.add(user_id)
        return allowed_roles, allowed_users

    @commands.slash_command(description="建立一個可定時或手動結束的投票")
    @discord.option(
        "title",
        description="投票的標題",
        type=discord.SlashCommandOptionType.string,
        required=True
    )
    @discord.option(
        "options_str",
        description="選項，請用「逗號」分隔 (例如: 選項A, 選項B)。選項上限為23個。",
        type=discord.SlashCommandOptionType.string,
        required=True
    )
    @discord.option(
        "duration",
        description="持續時間 (例: 1h 30m, 5m, 90s, 2d, forever)。預設為 1 天。",
        type=discord.SlashCommandOptionType.string,
        required=False
    )
    @discord.option(
        "allowed",
        description="允許投票的身分組或使用者 (提及，用空格分隔)。留空則所有人皆可",
        type=discord.SlashCommandOptionType.string,
        required=False
    )
    async def create_poll(self, ctx: discord.ApplicationContext, title: str, options_str: str, duration: str | None = None, allowed: str | None = None):
        # Split options, strip whitespace, and remove empty strings
        options = [opt.strip() for opt in options_str.split(',') if opt.strip()]

        # --- Input Validation ---
        if not options:
            await ctx.respond("請至少提供一個有效的選項 (選項之間請用逗號 `,` 分隔)。", ephemeral=True)
            return
        if len(options) < 2:
            await ctx.respond("投票至少需要 2 個選項。", ephemeral=True)
            return
        if len(options) > 23: # Discord button limit is 25 per view, keep some room
            await ctx.respond(f"最多只能建立 23 個選項，你提供了 {len(options)} 個。", ephemeral=True)
            return
        # Check for duplicate options (case-sensitive check)
        if len(options) != len(set(options)): # Removed .lower() for case-sensitivity
            await ctx.respond("投票選項不能重複 (區分大小寫)。", ephemeral=True) # Updated error message
            return
        # Check option length (Discord button label limit is 80)
        for opt in options:
             if len(opt) > 70: # Leave room for " (0)" count
                 await ctx.respond(f"選項 '{opt[:30]}...' 過長，請縮短至 70 字元內。", ephemeral=True)
                 return

        # --- Parse Duration ---
        duration_seconds: float | None = None # Initialize as None (permanent) by default
        one_day_seconds = 24 * 60 * 60

        if duration is None:
            # Default to 1 day if no duration is provided
            duration_seconds = one_day_seconds
        elif duration.strip().lower() == "forever":
            # Explicitly set to None for permanent poll
            duration_seconds = None
        else:
            # Try parsing the provided duration string
            duration_seconds = self.parse_duration(duration)
            if duration_seconds is None:
                # Parsing failed, and it wasn't "forever"
                await ctx.respond("無效的時間格式。請使用例如 `1h`, `30m`, `90s`, `2d`, 組合 `1h 30m`, 或 `forever`。", ephemeral=True)
                return
            elif duration_seconds <= 0:
                 await ctx.respond("持續時間必須大於 0 秒。", ephemeral=True)
                 return

        # --- Parse allowed roles/users (requires guild context) ---
        allowed_roles, allowed_users = set(), set()
        if allowed:
            if ctx.guild:
                 allowed_roles, allowed_users = self.parse_allowed(allowed, ctx.guild)
                 if not allowed_roles and not allowed_users:
                      await ctx.respond("提供的允許投票者無效 (找不到提及的身分組或使用者)。", ephemeral=True)
                      return
            else:
                 # Cannot use role/user restrictions in DMs
                 await ctx.respond("限制投票權限的功能僅能在伺服器內使用。", ephemeral=True)
                 return

        # --- Create and Send Poll ---
        # Defer response first, as creating view/embed is quick, sending might take time
        await ctx.defer(ephemeral=False) # Send public response

        view = PollView(
            bot=self.bot,
            title=title,
            options=options,
            allowed_roles=allowed_roles,
            allowed_users=allowed_users,
            author_id=ctx.author.id,
            duration=duration_seconds # Pass the calculated duration (can be None)
        )

        embed = view.create_embed()

        try:
            # Use followup.send after deferring
            poll_message = await ctx.followup.send(embed=embed, view=view, wait=True)
            # Store message and channel IDs in the view for later reference (e.g., timeout)
            view.message_id = poll_message.id
            view.channel_id = poll_message.channel.id
        except discord.HTTPException as e:
            print(f"Failed to send poll message: {e}")
            # Try sending an error message back to the user
            try:
                await ctx.followup.send("抱歉，建立投票時發生錯誤，無法傳送訊息。", ephemeral=True)
            except discord.HTTPException:
                print("Failed to send error message after poll creation failure.")
        except Exception as e: # Catch other potential errors
            print(f"An unexpected error occurred during poll creation: {e}")
            try:
                await ctx.followup.send("抱歉，建立投票時發生未預期的錯誤。", ephemeral=True)
            except discord.HTTPException:
                 print("Failed to send unexpected error message after poll creation failure.")

# The View class handling the poll buttons and logic
class PollView(discord.ui.View): # Inherit from discord.ui.View
    # Pass bot instance for fetching message on timeout
    def __init__(self, bot: commands.Bot, title: str, options: list[str], allowed_roles: set[int], allowed_users: set[int], author_id: int, duration: float | None = None):
        super().__init__(timeout=duration)
        self.bot = bot
        self.title = title
        self.options = options
        self.allowed_roles = allowed_roles
        self.allowed_users = allowed_users
        self.author_id = author_id
        self.duration = duration # Store duration if needed
        self.message_id: int | None = None # To be set after message is sent
        self.channel_id: int | None = None # To be set after message is sent
        self.ended = False # Flag to prevent double ending
        self.color = random.randint(0, 16777215) # Store a random color for this poll instance
        self.end_time: datetime | None = None # Store the end time if duration exists
        if duration:
            # Use timezone-aware datetime
            self.end_time = datetime.now(timezone.utc) + timedelta(seconds=duration)

        # Stores votes: {user_id: option_index}
        self.user_votes: dict[int, int] = {}
        # Stores vote counts: {option_index: count}
        self.vote_counts: defaultdict[int, int] = defaultdict(int)

        # --- Create Buttons ---
        # Option buttons
        for i, option_text in enumerate(options):
            # Initial label, vote count is 0
            label = f"{option_text[:70]}..." if len(option_text) > 70 else option_text
            # Use discord.ui.Button
            button = discord.ui.Button(label=f"{label} (0)", style=discord.ButtonStyle.secondary, custom_id=f"poll_option_{i}")
            button.callback = self.vote_callback
            self.add_item(button)

        # Retract Vote button
        # Use discord.ui.Button
        self.retract_button = discord.ui.Button(label="收回投票", style=discord.ButtonStyle.primary, custom_id="poll_retract")
        self.retract_button.callback = self.retract_vote_callback
        self.add_item(self.retract_button)

        # End Poll button (only creator can use)
        # Use discord.ui.Button
        self.end_button = discord.ui.Button(label="結束投票 (僅發起者)", style=discord.ButtonStyle.danger, custom_id="poll_end")
        self.end_button.callback = self.end_poll_callback
        self.add_item(self.end_button)

    def update_button_labels(self):
        for item in self.children:
            # Check for discord.ui.Button
            if isinstance(item, discord.ui.Button) and item.custom_id and item.custom_id.startswith("poll_option_"):
                try:
                    option_index = int(item.custom_id.split("_")[-1])
                    # Check if index is valid before accessing options/counts
                    if 0 <= option_index < len(self.options):
                        option_text = self.options[option_index]
                        count = self.vote_counts[option_index]
                        # Limit label length (Discord has limits)
                        base_label = option_text[:70] + '...' if len(option_text) > 70 else option_text
                        item.label = f"{base_label} ({count})"
                    else:
                        # Handle invalid index gracefully (e.g., disable button)
                        item.label = "(選項錯誤)"
                        item.disabled = True
                except (IndexError, ValueError):
                    item.label = "(錯誤)"
                    item.disabled = True # Disable if something is wrong

    def create_embed(self, ended: bool = False) -> discord.Embed:
        # Use the stored color, or grey if ended
        color = 0xAAAAAA if ended else self.color
        status = "(已結束)" if ended else ""
        embed = discord.Embed(title=f"📊 {self.title} {status}", color=color)
        total_votes = sum(self.vote_counts.values())

        if ended:
            # --- Show final results ---
            results_str = ""
            winner_str = "" # String to hold winner/tie info

            if total_votes == 0:
                results_str = "沒有人投票。"
                winner_str = "無結果"
            else:
                # Sort results by vote count (descending)
                sorted_results = sorted(self.vote_counts.items(), key=lambda item: item[1], reverse=True)

                # Build results string
                for option_index, count in sorted_results:
                    try:
                        option_text = self.options[option_index]
                        percentage = (count / total_votes) * 100
                        results_str += f"- {option_text}: {count} 票 ({percentage:.1f}%)\n"
                    except IndexError:
                        results_str += f"- (未知選項 {option_index}): {count} 票\n"

                # Determine winner(s)
                if sorted_results: # Ensure there are results before accessing index 0
                    highest_vote_count = sorted_results[0][1]
                    winners = []
                    for option_index, count in sorted_results:
                        if count == highest_vote_count:
                            try:
                                winners.append(self.options[option_index])
                            except IndexError:
                                winners.append(f"(未知選項 {option_index})")
                        else:
                            # Since it's sorted, we can stop early
                            break

                    if len(winners) == 1:
                        winner_str = f"🏆 **獲勝者: {winners[0]}**"
                    elif len(winners) > 1:
                        winner_str = f"🤝 **平手: {', '.join(winners)}**"
                    else: # Should not happen if sorted_results is not empty
                        winner_str = "無結果"
                else: # Case where vote_counts was somehow non-empty but sorted_results is empty
                    winner_str = "計算結果時發生錯誤"


            embed.description = f"投票結果如下：\n{winner_str}" # Add winner info to description
            # Ensure results string doesn't exceed limit
            if len(results_str) > 1024:
                results_str = results_str[:1020] + "\n..." # Truncate if too long
            embed.add_field(name="最終票數", value=results_str if results_str else "無", inline=False) # Renamed field
            embed.set_footer(text=f"總投票數: {total_votes}")
        else:
            # --- Show ongoing poll info with bar chart ---
            embed.description = "點擊下方按鈕進行投票！"

            # --- Add Bar Chart Field ---
            field_value = "" # Initialize field value

            if total_votes == 0:
                field_value = "目前尚無人投票。"
            else:
                # Constants for bar chart formatting
                option_text_width = 33
                bar_char_filled = '█'
                bar_char_empty = '░'
                max_bar_width = 40

                # Prepare lines data and calculate max length for count/percentage part
                lines_data = []
                max_count_percent_len = 0
                for i, option_text in enumerate(self.options):
                    if not (0 <= i < len(self.options)): continue
                    count = self.vote_counts[i]
                    percentage = (count / total_votes) * 100 if total_votes > 0 else 0
                    count_percent_part = f" | {count} ({percentage:.1f}%)"
                    max_count_percent_len = max(max_count_percent_len, len(count_percent_part))
                    # Store index along with other data for sorting
                    lines_data.append({'index': i, 'text': option_text, 'count': count, 'percentage': percentage, 'count_percent_part': count_percent_part})

                # Sort data by vote count (descending)
                sorted_lines_data = sorted(lines_data, key=lambda item: item['count'], reverse=True)

                # --- Function to generate bar chart lines for given data ---
                def generate_chart_lines(data_subset):
                    chart_lines = []
                    # Recalculate max_count_percent_len based *only* on the subset
                    subset_max_count_percent_len = 0
                    if data_subset: # Ensure subset is not empty
                        subset_max_count_percent_len = max(len(item['count_percent_part']) for item in data_subset)

                    total_text_width = option_text_width + subset_max_count_percent_len # Use subset max length

                    for item in data_subset:
                        option_text = item['text']
                        count_percent_part = item['count_percent_part']
                        percentage = item['percentage']

                        display_option = option_text[:option_text_width-3] + '...' if len(option_text) > option_text_width else option_text
                        # Pad using the subset's max length
                        padded_option = f"{display_option:<{option_text_width}}"
                        padded_count_percent = f"{count_percent_part:<{subset_max_count_percent_len}}"
                        text_line = f"{padded_option}{padded_count_percent}"

                        filled_blocks = min(round((percentage / 100) * max_bar_width), max_bar_width)
                        empty_blocks = max_bar_width - filled_blocks
                        bar = bar_char_filled * filled_blocks + bar_char_empty * empty_blocks

                        chart_lines.append(f"`{text_line}`\n`{bar}`")
                    return chart_lines
                # --- End of helper function ---

                # Generate lines for all options first to check total length
                num_options_to_show = len(sorted_lines_data)
                current_bar_chart_str = ""

                while num_options_to_show > 0:
                    data_subset = sorted_lines_data[:num_options_to_show]
                    current_chart_lines = generate_chart_lines(data_subset)
                    current_bar_chart_str = "\n".join(current_chart_lines)

                    if len(current_bar_chart_str) <= 1000:
                        # Found a length that fits
                        break
                    else:
                        # Too long, reduce the number of options and try again
                        num_options_to_show -= 1

                # --- Determine final field value ---
                if num_options_to_show == 0:
                     # Even showing 1 option was too long (or no options somehow)
                     field_value = "票數資訊過長，無法顯示圖表。"
                elif num_options_to_show == len(sorted_lines_data):
                     # The full chart fits
                     field_value = current_bar_chart_str
                else:
                     # Partial chart fits, add a note
                     field_value = f"{current_bar_chart_str}\n*（票數資訊過長，僅顯示前 {num_options_to_show} 名）*"

            # Use the determined field_value
            embed.add_field(name="目前票數", value=field_value, inline=False)
            # --- End Bar Chart Field ---

            if self.allowed_roles or self.allowed_users:
                allowed_mentions = []
                if self.allowed_roles:
                    allowed_mentions.extend(f"<@&{rid}>" for rid in self.allowed_roles)
                if self.allowed_users:
                    allowed_mentions.extend(f"<@{uid}>" for uid in self.allowed_users)
                # Check length before adding field
                allowed_value = " ".join(allowed_mentions) if allowed_mentions else "無"
                if len(allowed_value) <= 1024: # Discord field value limit
                    embed.add_field(name="可投票者", value=allowed_value, inline=False)
                else:
                    embed.add_field(name="可投票者", value="（提及列表過長）", inline=False)


            # Use the stored end_time if available
            if self.end_time:
                # Use discord's timestamp formatting
                end_timestamp = int(self.end_time.timestamp())
                embed.add_field(name="預計結束時間", value=f"<t:{end_timestamp}:R> (<t:{end_timestamp}:F>)", inline=False)
            elif self.duration is None: # Explicitly permanent poll
                 embed.add_field(name="持續時間", value="永久", inline=False)


            embed.set_footer(text=f"總投票數: {total_votes}")

        return embed

    def disable_all_items(self):
        for item in self.children:
            # Check for discord.ui.Button
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def end_poll(self, interaction: discord.Interaction | None):
        if self.ended: return # Already ended
        self.ended = True
        self.disable_all_items()
        final_embed = self.create_embed(ended=True) # Create final results embed

        original_message_edited = False
        original_message: discord.Message | None = None

        # --- Try to Edit the Original Message ---
        try:
            if interaction: # Ended manually via button
                # Edit the message the button is attached to
                await interaction.response.edit_message(embed=final_embed, view=self)
                original_message_edited = True
                original_message = interaction.message # Store the message object
            elif self.message_id and self.channel_id: # Ended via timeout or other means without interaction
                channel = self.bot.get_channel(self.channel_id)
                # Ensure channel is a type that can have messages fetched/edited
                if channel and isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
                    try:
                        message = await channel.fetch_message(self.message_id)
                        await message.edit(embed=final_embed, view=self)
                        original_message_edited = True
                        original_message = message # Store the message object
                    except discord.NotFound:
                        print(f"Warning: Original poll message {self.message_id} not found for editing.")
                    except discord.Forbidden:
                        print(f"Warning: Bot lacks permissions to edit original poll message {self.message_id} in channel {self.channel_id}.")
                    except discord.HTTPException as e:
                        print(f"Warning: Failed to edit original poll message {self.message_id}: {e}")
                else:
                    print(f"Warning: Could not find valid channel {self.channel_id} for poll {self.message_id}. Cannot edit original message.")
            else:
                 print(f"Warning: Poll ended but message_id/channel_id missing. Cannot edit original message.")

        except discord.NotFound: # Catch potential NotFound from interaction.response.edit_message
             print(f"Warning: Failed to edit poll message via interaction (Not Found). Maybe deleted?")
        except discord.Forbidden:
             print(f"Warning: Bot lacks permissions to edit poll message via interaction in channel {self.channel_id}.")
        except discord.HTTPException as e:
            print(f"Warning: Failed to edit poll message via interaction: {e}")
        finally:
            self.stop() # Stop the view listener regardless of edit success

        # --- Send Final Results as a New Message ---
        if self.channel_id:
            channel = self.bot.get_channel(self.channel_id)
            if channel and isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
                try:
                    # Create a reference to the original poll message if we successfully edited/fetched it
                    message_reference = None
                    if original_message:
                        message_reference = original_message.to_reference(fail_if_not_exists=False) # Don't error if original deleted between edit and send

                    await channel.send(
                        content=f"📊 **{self.title}** 投票已結束！", # Add context text
                        embed=final_embed,
                        reference=message_reference, # Reply to the original poll message
                        allowed_mentions=discord.AllowedMentions.none() # Avoid pinging people in results
                    )
                except discord.Forbidden:
                    print(f"Error: Bot lacks permissions to send final results message in channel {self.channel_id}.")
                except discord.HTTPException as e:
                    print(f"Error: Failed to send final results message in channel {self.channel_id}: {e}")
            else:
                print(f"Error: Could not find valid channel {self.channel_id} to send final results message.")
        else:
            print("Error: channel_id missing, cannot send final results message.")

    async def on_timeout(self):
        print(f"Poll view timed out for message {self.message_id} in channel {self.channel_id}")
        if not self.ended: # Check if not already ended manually
            await self.end_poll(interaction=None) # End the poll, passing None for interaction

    def check_permissions(self, user: discord.User | discord.Member, guild: discord.Guild | None) -> bool:
        # If no restrictions, allow everyone
        if not self.allowed_roles and not self.allowed_users:
            return True

        # Check if user is specifically allowed
        if user.id in self.allowed_users:
            return True

        # Check if user has an allowed role (only works in guilds)
        if guild and isinstance(user, discord.Member) and self.allowed_roles:
            user_role_ids = {role.id for role in user.roles}
            # Check for intersection between user roles and allowed roles
            if not user_role_ids.isdisjoint(self.allowed_roles):
                return True

        # If none of the above, deny
        return False

    # --- Button Callbacks ---

    async def vote_callback(self, interaction: discord.Interaction):
        # Ensure the poll hasn't ended before processing vote
        if self.ended:
            await interaction.response.send_message("抱歉，此投票已結束。", ephemeral=True)
            return

        user = interaction.user
        guild = interaction.guild
        user_id = user.id

        # --- Permission Check ---
        if not self.check_permissions(user, guild):
            await interaction.response.send_message("抱歉，你沒有權限參與這次投票。", ephemeral=True)
            return

        # --- Get Selected Option ---
        # interaction.data is a dict containing component data
        button_custom_id = interaction.data.get('custom_id')
        if not button_custom_id or not button_custom_id.startswith("poll_option_"):
             await interaction.response.send_message("無效的按鈕。", ephemeral=True)
             return
        try:
            # Extract index from custom_id like "poll_option_2"
            option_index = int(button_custom_id.split("_")[-1])
            # Validate index against the number of options
            if not (0 <= option_index < len(self.options)):
                 await interaction.response.send_message("投票選項無效。", ephemeral=True)
                 return
        except (IndexError, ValueError):
            await interaction.response.send_message("處理投票時發生錯誤。", ephemeral=True)
            return

        # --- Handle Vote Change/Initial Vote ---
        previous_vote = self.user_votes.get(user_id)

        # If user clicked the same option they already voted for, do nothing except acknowledge
        if previous_vote == option_index:
            await interaction.response.defer() # Acknowledge interaction
            return

        # Atomically update votes
        if previous_vote is not None: # User is changing their vote
            self.vote_counts[previous_vote] = max(0, self.vote_counts[previous_vote] - 1) # Decrement old, ensure >= 0
        self.user_votes[user_id] = option_index # Set new vote
        self.vote_counts[option_index] += 1 # Increment new vote count

        # --- Update Message and Respond ---
        self.update_button_labels()
        new_embed = self.create_embed() # Get updated embed with bar chart
        try:
            # Edit the original message with the updated embed and view
            await interaction.response.edit_message(embed=new_embed, view=self)
        except discord.NotFound:
            print(f"Failed to edit poll message {self.message_id} on vote (Not Found).")
        except discord.HTTPException as e:
            print(f"Failed to edit poll message {self.message_id} on vote: {e}")


    async def retract_vote_callback(self, interaction: discord.Interaction):
        # Ensure the poll hasn't ended
        if self.ended:
            await interaction.response.send_message("抱歉，此投票已結束。", ephemeral=True)
            return

        user = interaction.user
        guild = interaction.guild
        user_id = user.id

        # --- Permission Check (Good practice, though maybe redundant if they voted) ---
        if not self.check_permissions(user, guild):
            # This case might be less likely if they already voted, but good to have
            await interaction.response.send_message("抱歉，你沒有權限操作這次投票。", ephemeral=True)
            return

        # --- Check if User Has Voted ---
        if user_id not in self.user_votes:
            await interaction.response.send_message("你尚未投票，無法收回。", ephemeral=True)
            return

        # --- Retract Vote ---
        try:
            old_vote_index = self.user_votes.pop(user_id) # Remove user's vote mapping
            self.vote_counts[old_vote_index] = max(0, self.vote_counts[old_vote_index] - 1) # Decrement count, ensure >= 0
        except KeyError:
             # Should not happen if user_id was in self.user_votes, but handle defensively
             await interaction.response.send_message("收回投票時發生錯誤。", ephemeral=True)
             return

        # --- Update Message and Respond ---
        self.update_button_labels()
        new_embed = self.create_embed() # Get updated embed with bar chart
        try:
            # Edit the original message with the updated embed and view
            await interaction.response.edit_message(embed=new_embed, view=self)
            # Send ephemeral confirmation for retraction AFTER successful edit
            await interaction.followup.send("你的投票已成功收回。", ephemeral=True)
        except discord.NotFound:
            print(f"Failed to edit poll message {self.message_id} on retract (Not Found).")
            # Try sending followup even if edit failed
            try:
                await interaction.followup.send("你的投票已成功收回 (訊息更新失敗)。", ephemeral=True)
            except discord.HTTPException: pass # Ignore if followup also fails
        except discord.HTTPException as e:
            print(f"Failed to edit poll message {self.message_id} on retract: {e}")
            # Try sending followup even if edit failed
            try:
                await interaction.followup.send("你的投票已成功收回 (訊息更新失敗)。", ephemeral=True)
            except discord.HTTPException: pass # Ignore if followup also fails


    async def end_poll_callback(self, interaction: discord.Interaction):
        # --- Check if User is the Author ---
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("只有發起投票的人才能結束投票。", ephemeral=True)
            return

        # --- End the Poll ---
        if not self.ended:
            # Pass interaction so end_poll knows it was triggered by a button
            # and can use interaction.response.edit_message
            await self.end_poll(interaction=interaction)
        else:
            # If already ended (e.g., race condition), just acknowledge
            await interaction.response.defer()

def setup(bot):
    bot.add_cog(Poll(bot))