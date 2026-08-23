import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import asyncio

class YapJail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jailed_users = {}
        self.jail_file = "data/jailed_users.json"
        self.ensure_data_directory()
        self.load_jailed_users()

    def ensure_data_directory(self):
        """Ensure the data directory exists"""
        if not os.path.exists("data"):
            os.makedirs("data")

    def load_jailed_users(self):
        """Load jailed users from file"""
        if os.path.exists(self.jail_file):
            try:
                with open(self.jail_file, 'r') as f:
                    data = json.load(f)
                    for user_id, info in data.items():
                        info['jailed_at'] = datetime.fromisoformat(info['jailed_at'])
                        self.jailed_users[int(user_id)] = info
                print(f"✅ Loaded {len(self.jailed_users)} jailed users from file")
            except Exception as e:
                print(f"❌ Error loading jailed users: {e}")
        else:
            print("📝 No existing jail data found, starting fresh")

    def save_jailed_users(self):
        """Save jailed users to file"""
        try:
            data = {}
            for user_id, info in self.jailed_users.items():
                data[str(user_id)] = {
                    "jailed_at": info['jailed_at'].isoformat(),
                    "guild_id": info['guild_id'],
                    "jail_time": info.get('jail_time', 0),
                    "forced": info.get('forced', False),  # Add forced flag
                    "jailed_by": info.get('jailed_by', 'self')
                }
            with open(self.jail_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"💾 Saved {len(self.jailed_users)} jailed users to file")
        except Exception as e:
            print(f"❌ Error saving jailed users: {e}")

    async def apply_jail_restrictions(self, member: discord.Member, forced: bool = False, jailed_by: str = "self"):
        """Apply restrictions to jailed user - prevents speaking and chatting"""
        try:
            # Create/assign jail role
            jail_role = discord.utils.get(member.guild.roles, name="YapJailed")
            if not jail_role:
                jail_role = await member.guild.create_role(
                    name="YapJailed",
                    reason="YapJail: Role for jailed users",
                    permissions=discord.Permissions.none()
                )
            
            # Assign jail role
            await member.add_roles(jail_role, reason="YapJail: User is jailed")
            print(f"✅ Added YapJailed role to {member.display_name}")

            # SERVER MUTE - Most effective way to mute in voice
            if member.voice and member.voice.channel:
                try:
                    await member.edit(mute=True, reason="YapJail: User is jailed")
                    print(f"🔇 Server muted {member.display_name}")
                except Exception as e:
                    print(f"❌ Failed to server mute {member.display_name}: {e}")

            # Apply voice channel permissions - DISABLE speak PER CHANNEL
            for channel in member.guild.voice_channels:
                try:
                    overwrite = discord.PermissionOverwrite()
                    overwrite.speak = False
                    overwrite.connect = None
                    overwrite.stream = None
                    
                    await channel.set_permissions(
                        member,
                        overwrite=overwrite,
                        reason="YapJail: Disabled microphone in voice channel"
                    )
                    print(f"🔇 Set voice permissions for {member.display_name} in {channel.name}")
                except Exception as e:
                    print(f"❌ Error setting permissions in {channel.name}: {e}")

            # Disable text chat INSIDE voice channels
            for channel in member.guild.voice_channels:
                try:
                    overwrite = discord.PermissionOverwrite()
                    overwrite.send_messages = False
                    overwrite.add_reactions = False
                    overwrite.create_public_threads = False
                    overwrite.create_private_threads = False
                    overwrite.send_messages_in_threads = False
                    
                    await channel.set_permissions(
                        member,
                        overwrite=overwrite,
                        reason="YapJail: Disabled voice channel text chat"
                    )
                    print(f"🔇 Disabled voice text chat for {member.display_name} in {channel.name}")
                except Exception as e:
                    print(f"❌ Error disabling voice text chat in {channel.name}: {e}")

            # RESTRICT ALL REGULAR TEXT CHANNELS
            for channel in member.guild.text_channels:
                try:
                    if channel.name.lower() == "yap-jail":
                        continue
                    
                    overwrite = discord.PermissionOverwrite()
                    overwrite.send_messages = False
                    overwrite.add_reactions = False
                    overwrite.create_public_threads = False
                    overwrite.create_private_threads = False
                    overwrite.send_messages_in_threads = False
                    overwrite.read_messages = None
                    overwrite.read_message_history = None
                    
                    await channel.set_permissions(
                        member,
                        overwrite=overwrite,
                        reason="YapJail: Disabled chat in text channels"
                    )
                    print(f"🔇 Set text permissions for {member.display_name} in #{channel.name}")
                except Exception as e:
                    print(f"❌ Error setting permissions in #{channel.name}: {e}")

            print(f"✅ Applied jail restrictions to {member.display_name}")
            return True
        except Exception as e:
            print(f"❌ Error applying jail restrictions to {member.display_name}: {e}")
            return False

    async def remove_jail_restrictions(self, member: discord.Member):
        """Remove all jail restrictions from user"""
        try:
            print(f"🔓 Starting unjail process for {member.display_name}")
            
            # 1. SERVER UNMUTE - Remove server mute
            if member.voice and member.voice.channel:
                try:
                    await member.edit(mute=False, reason="YapJail: User freed")
                    print(f"🔊 Server unmuted {member.display_name}")
                except Exception as e:
                    print(f"❌ Failed to server unmute {member.display_name}: {e}")

            # 2. Remove jail role
            jail_role = discord.utils.get(member.guild.roles, name="YapJailed")
            if jail_role and jail_role in member.roles:
                try:
                    await member.remove_roles(jail_role, reason="YapJail: User freed")
                    print(f"✅ Removed YapJailed role from {member.display_name}")
                except Exception as e:
                    print(f"❌ Failed to remove jail role: {e}")

            # 3. Reset ALL voice channel permissions (including text chat)
            for channel in member.guild.voice_channels:
                try:
                    await channel.set_permissions(member, overwrite=None)
                    print(f"🔓 Reset voice permissions for {member.display_name} in {channel.name}")
                except Exception as e:
                    print(f"❌ Error resetting voice permissions in {channel.name}: {e}")

            # 4. Reset ALL text channel permissions
            for channel in member.guild.text_channels:
                try:
                    if channel.name.lower() != "yap-jail":
                        await channel.set_permissions(member, overwrite=None)
                        print(f"🔓 Reset text permissions for {member.display_name} in #{channel.name}")
                except Exception as e:
                    print(f"❌ Error resetting text permissions in #{channel.name}: {e}")

            # 5. Reset YapJailed role permissions (if the role still exists)
            if jail_role:
                for channel in member.guild.voice_channels:
                    try:
                        await channel.set_permissions(jail_role, overwrite=None)
                        print(f"🔓 Reset role permissions in voice channel {channel.name}")
                    except Exception as e:
                        print(f"❌ Error resetting role permissions in {channel.name}: {e}")
                
                for channel in member.guild.text_channels:
                    try:
                        if channel.name.lower() != "yap-jail":
                            await channel.set_permissions(jail_role, overwrite=None)
                            print(f"🔓 Reset role permissions in #{channel.name}")
                    except Exception as e:
                        print(f"❌ Error resetting role permissions in #{channel.name}: {e}")

            print(f"✅ Successfully removed all jail restrictions from {member.display_name}")
            return True
        except Exception as e:
            print(f"❌ Error removing jail restrictions from {member.display_name}: {e}")
            return False

    @app_commands.command(name="yapjail", description="Put yourself in yap jail for a specified time")
    @app_commands.describe(
        time="Time in minutes (e.g., 5, 10, 30)",
        reason="Reason for going to yap jail (optional)"
    )
    async def yapjail(self, interaction: discord.Interaction, time: int, reason: str = "No reason provided"):
        """Command to jail yourself"""
        
        if interaction.user.id in self.jailed_users:
            # Check if it's a forced jail
            if self.jailed_users[interaction.user.id].get('forced', False):
                await interaction.response.send_message(
                    f"❌ You're in a **forced** yap jail! You cannot free yourself. An admin must free you with `/yapfree_admin`.",
                    ephemeral=True
                )
                return
            else:
                await interaction.response.send_message(
                    f"❌ You're already in yap jail! Use `/yapfree` to free yourself.",
                    ephemeral=True
                )
            return

        if time <= 0 or time > 1440:
            await interaction.response.send_message(
                "❌ Time must be between 1 and 1440 minutes (24 hours).",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        success = await self.apply_jail_restrictions(interaction.user)

        if not success:
            await interaction.followup.send(
                "❌ Failed to apply jail restrictions. Please check bot permissions.",
                ephemeral=True
            )
            return

        self.jailed_users[interaction.user.id] = {
            "jailed_at": datetime.now(),
            "guild_id": interaction.guild_id,
            "jail_time": time,
            "forced": False,
            "jailed_by": "self"
        }
        self.save_jailed_users()

        embed = discord.Embed(
            title="🔒 Yap Jail Initiated",
            description=f"**{interaction.user.display_name}** has put themselves in yap jail!",
            color=discord.Color.red()
        )
        embed.add_field(name="⏱️ Time", value=f"{time} minutes", inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(
            name="🔇 Restrictions", 
            value="❌ Cannot speak in voice channels (server muted)\n❌ Cannot send messages in voice text chat\n❌ Cannot send messages in regular text channels\n✅ Can read messages\n✅ Can join voice channels\n✅ Can use camera\n✅ Can screen share\n✅ Can listen to others",
            inline=False
        )
        embed.add_field(
            name="🔓 Freedom", 
            value="You can free yourself at any time with `/yapfree`",
            inline=False
        )
        embed.set_footer(text="You will be automatically freed after the time expires")

        await interaction.followup.send(embed=embed)
        await self.schedule_auto_free(interaction.user, time)

    @app_commands.command(name="yapfree", description="Free yourself from yap jail")
    async def yapfree(self, interaction: discord.Interaction):
        """Command to free yourself from yap jail - works in DMs"""
        
        # Check if user is in a DM
        if interaction.guild is None:
            # User is in DMs
            user_id = interaction.user.id
            
            if user_id not in self.jailed_users:
                await interaction.response.send_message(
                    "❌ You're not currently in yap jail in any server!",
                    ephemeral=True
                )
                return
            
            # Check if it's a forced jail
            if self.jailed_users[user_id].get('forced', False):
                await interaction.response.send_message(
                    "❌ You're in a **forced** yap jail! You cannot free yourself. An admin must free you.",
                    ephemeral=True
                )
                return
            
            guild_id = self.jailed_users[user_id]["guild_id"]
            guild = self.bot.get_guild(guild_id)
            
            if not guild:
                await interaction.response.send_message(
                    "❌ Could not find the server you're jailed in!",
                    ephemeral=True
                )
                return
            
            member = guild.get_member(user_id)
            if not member:
                del self.jailed_users[user_id]
                self.save_jailed_users()
                await interaction.response.send_message(
                    "❌ You're no longer in that server!",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            success = await self.remove_jail_restrictions(member)
            
            if success:
                del self.jailed_users[user_id]
                self.save_jailed_users()
                await interaction.followup.send(
                    f"🔓 You've been freed from yap jail in **{guild.name}**! 🎉",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ Failed to free you. Please contact an admin!",
                    ephemeral=True
                )
            return
        
        # User is in a server
        if interaction.user.id not in self.jailed_users:
            await interaction.response.send_message(
                "❌ You're not currently in yap jail!",
                ephemeral=True
            )
            return

        # Check if it's a forced jail
        if self.jailed_users[interaction.user.id].get('forced', False):
            await interaction.response.send_message(
                "❌ You're in a **forced** yap jail! You cannot free yourself. An admin must free you with `/yapfree_admin`.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        success = await self.remove_jail_restrictions(interaction.user)

        if not success:
            await interaction.followup.send(
                "❌ Failed to free you. Please contact an admin!",
                ephemeral=True
            )
            return

        del self.jailed_users[interaction.user.id]
        self.save_jailed_users()

        embed = discord.Embed(
            title="🔓 Freed from Yap Jail!",
            description=f"**{interaction.user.display_name}** has been freed! 🎉",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📢 Message from Jailer",
            value="You're free to yap again! You can now use your microphone, chat, camera, and screen share.",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="yapfree_admin", description="Admin: Free someone from yap jail")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        user="The user to free from yap jail",
        reason="Reason for freeing (optional)"
    )
    async def yapfree_admin(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Admin command to free someone from yap jail - can free forced jails too"""
        
        if user.id not in self.jailed_users:
            await interaction.response.send_message(
                f"❌ {user.display_name} is not currently in yap jail!",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        jail_info = self.jailed_users.get(user.id, {})
        jail_time = jail_info.get('jail_time', 'unknown')
        was_forced = jail_info.get('forced', False)

        success = await self.remove_jail_restrictions(user)

        if not success:
            await interaction.followup.send(
                f"❌ Failed to free {user.display_name}. Please check bot permissions!",
                ephemeral=True
            )
            return

        del self.jailed_users[user.id]
        self.save_jailed_users()

        embed = discord.Embed(
            title="🔓 Admin Yap Free",
            description=f"**{user.display_name}** has been freed from yap jail by {interaction.user.display_name}! 🎉",
            color=discord.Color.green()
        )
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        embed.add_field(name="👤 Freed By", value=interaction.user.display_name, inline=True)
        embed.add_field(name="⏱️ Original Jail Time", value=f"{jail_time} minutes", inline=True)
        if was_forced:
            embed.add_field(name="🔒 Type", value="Forced Jail (Admin Only)", inline=True)
        else:
            embed.add_field(name="🔓 Type", value="Voluntary Jail", inline=True)

        await interaction.followup.send(embed=embed)

        try:
            dm_embed = discord.Embed(
                title="🔓 You've Been Freed!",
                description=f"You have been freed from yap jail in **{interaction.guild.name}**!",
                color=discord.Color.green()
            )
            dm_embed.add_field(name="👤 Freed By", value=f"{interaction.user.display_name} (Admin)", inline=True)
            dm_embed.add_field(name="📝 Reason", value=reason, inline=True)
            await user.send(embed=dm_embed)
        except:
            pass

    @app_commands.command(name="yapjail_admin", description="Admin: Jail another user")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        user="The user to jail",
        time="Time in minutes",
        reason="Reason for jailing",
        forced="If True, user cannot free themselves (default: False)"
    )
    async def admin_jail(self, interaction: discord.Interaction, user: discord.Member, time: int, reason: str = "No reason provided", forced: bool = False):
        """Admin command to jail another user"""
        
        if user.id in self.jailed_users:
            # Check if it's a forced jail
            if self.jailed_users[user.id].get('forced', False):
                await interaction.response.send_message(
                    f"❌ {user.display_name} is already in a **forced** yap jail! Use `/yapfree_admin` to free them first.",
                    ephemeral=True
                )
                return
            else:
                await interaction.response.send_message(
                    f"❌ {user.display_name} is already in yap jail!",
                    ephemeral=True
                )
            return

        if time <= 0 or time > 1440:
            await interaction.response.send_message(
                "❌ Time must be between 1 and 1440 minutes.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        success = await self.apply_jail_restrictions(user, forced=forced, jailed_by="admin")
        
        if not success:
            await interaction.followup.send(
                f"❌ Failed to jail {user.display_name}. Please check bot permissions!",
                ephemeral=True
            )
            return

        self.jailed_users[user.id] = {
            "jailed_at": datetime.now(),
            "guild_id": interaction.guild_id,
            "jail_time": time,
            "forced": forced,
            "jailed_by": "admin"
        }
        self.save_jailed_users()

        embed = discord.Embed(
            title="🔒 Admin Yap Jail",
            description=f"**{user.display_name}** has been put in yap jail by {interaction.user.display_name}!",
            color=discord.Color.red()
        )
        embed.add_field(name="⏱️ Time", value=f"{time} minutes", inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        if forced:
            embed.add_field(
                name="🔒 Type", 
                value="**FORCED JAIL** - User cannot free themselves!",
                inline=False
            )
            embed.add_field(
                name="🔓 How to Free", 
                value="Only an admin can free this user with `/yapfree_admin`",
                inline=False
            )
        else:
            embed.add_field(
                name="🔓 Type", 
                value="Voluntary - User can free themselves with `/yapfree`",
                inline=False
            )
        embed.add_field(
            name="🔇 Restrictions", 
            value="❌ Cannot speak in voice channels (server muted)\n❌ Cannot send messages in voice text chat\n❌ Cannot send messages in regular text channels\n✅ Can read messages\n✅ Can join voice channels\n✅ Can use camera\n✅ Can screen share\n✅ Can listen to others",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        await self.schedule_auto_free(user, time)

    @app_commands.command(name="yapjail_list", description="List all currently jailed users")
    @app_commands.default_permissions(administrator=True)
    async def jail_list(self, interaction: discord.Interaction):
        """Admin command to see all jailed users"""
        
        if not self.jailed_users:
            await interaction.response.send_message(
                "📋 No users are currently in yap jail.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⛓️ Currently Jailed Users",
            color=discord.Color.orange()
        )
        
        for user_id, info in self.jailed_users.items():
            member = interaction.guild.get_member(user_id)
            name = member.display_name if member else f"User {user_id}"
            
            jailed_at = info['jailed_at']
            time_remaining = info.get('jail_time', 0)
            elapsed = (datetime.now() - jailed_at).total_seconds() / 60
            remaining = max(0, time_remaining - elapsed)
            forced = info.get('forced', False)
            jailed_by = info.get('jailed_by', 'self')
            
            status = "🔒 FORCED" if forced else "🔓 Voluntary"
            jailer = "Self" if jailed_by == "self" else "Admin"
            
            embed.add_field(
                name=f"{name} {status}",
                value=f"⏱️ {int(remaining)} minutes remaining\n📅 Jailed at: {jailed_at.strftime('%H:%M')}\n👤 Jailed by: {jailer}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def schedule_auto_free(self, user: discord.User, minutes: int):
        """Schedule automatic freeing after specified minutes"""
        await asyncio.sleep(minutes * 60)
        
        if user.id in self.jailed_users:
            guild_id = self.jailed_users[user.id]["guild_id"]
            guild = self.bot.get_guild(guild_id)
            if guild:
                member = guild.get_member(user.id)
                if member:
                    await self.remove_jail_restrictions(member)
                    del self.jailed_users[user.id]
                    self.save_jailed_users()

                    try:
                        await user.send(
                            f"🔓 Your yap jail time is up! You've been automatically freed in **{guild.name}**."
                        )
                    except:
                        pass

    @app_commands.command(name="yapjail_status", description="Check your yap jail status")
    async def jail_status(self, interaction: discord.Interaction):
        """Check current yap jail status"""
        
        if interaction.user.id in self.jailed_users:
            info = self.jailed_users[interaction.user.id]
            jailed_at = info['jailed_at']
            time_remaining = info.get('jail_time', 0)
            forced = info.get('forced', False)
            
            elapsed = (datetime.now() - jailed_at).total_seconds() / 60
            remaining = max(0, time_remaining - elapsed)
            
            embed = discord.Embed(
                title="⛓️ Yap Jail Status",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="📅 Jailed Since",
                value=jailed_at.strftime("%Y-%m-%d %H:%M:%S"),
                inline=False
            )
            embed.add_field(
                name="⏱️ Time Remaining",
                value=f"{int(remaining)} minutes",
                inline=False
            )
            embed.add_field(
                name="🔒 Type",
                value="🔒 FORCED - Cannot self-free" if forced else "🔓 Voluntary - Can use `/yapfree`",
                inline=False
            )
            embed.add_field(
                name="🔇 Current Restrictions",
                value="❌ Microphone disabled (server muted)\n❌ Cannot send messages in voice text chat\n❌ Cannot send messages in regular text channels\n✅ Can read messages\n✅ Voice channel access\n✅ Camera access\n✅ Screen sharing access",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                "✅ You are not currently in yap jail!",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(YapJail(bot))