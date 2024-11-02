import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
import requests
import json

# Create embeds for weather command

def weather_embed(data):
    city_name = data['city']['name']
    country = data['city']['country']
    lat = data['city']['coord']['lat']
    lon = data['city']['coord']['lon']
    forecast_list = data['list']

    # Create the embed
    embed = discord.Embed(
        title=f"Dự báo thời tiết cho {city_name}, {country}",
        description=f"Vị trí: {lat}, {lon}",
        color=discord.Color.blue()
    )

    embed.set_thumbnail(url=data['city']['url'])  # City image from response

    # Add summary information (first entry only for brevity)
    entry = forecast_list[0]
    temp = entry['main']['temp'] - 273.15  # Convert from Kelvin to Celsius
    feels_like = entry['main']['feels_like'] - 273.15
    description = entry['weather'][0]['description'].capitalize()
    wind_speed = entry['wind']['speed']
    humidity = entry['main']['humidity']

    embed.add_field(
        name=f"📅 {entry['dt_txt']}",
        value=(
            f"🌡️ Nhiệt độ: {temp:.2f}°C (Cảm giác như {feels_like:.2f}°C)\n"
            f"☁️ {description}\n"
            f"💨 Sức gió: {wind_speed} m/s | 💧 Độ ẩm: {humidity}%"
        ),
        inline=False
    )

    # Add only the next two entries (simplified)
    for entry in forecast_list[1:3]:
        dt = entry['dt_txt']
        temp = entry['main']['temp'] - 273.15
        description = entry['weather'][0]['description'].capitalize()

        embed.add_field(
            name=f"📅 {dt}",
            value=(
                f"🌡️ Nhiệt độ: {temp:.2f}°C\n"
                f"☁️ {description}"
            ),
            inline=False
        )

    embed.set_footer(text="Được cung cấp bởi RapidAPI")
    return embed

def wiki_embed(data):
    query = data['searchParameters']['q']
    img = None
    if 'knowledgeGraph' in data:
        info = data['knowledgeGraph']['description'].replace("...", "")
        img=data['knowledgeGraph']['imageUrl']
    else:
        info = data['organic'][0]['snippet']
    result = info.rsplit('.', 1)[0]
    
    embed = discord.Embed(
        title = f"Kết quả tìm kiếm của {query}",
        description = result,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=img)
    
    embed.set_footer(text="Được cung cấp bởi Serper Dev")
    return embed

# Create a new cog class

class Utility(commands.Cog, name="utility"):
    
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="help", description="Trả về danh sách các lệnh của bot")
    async def help(self, context: Context) -> None:
        prefix = self.bot.config["prefix"]
        embed = discord.Embed(
            title="Hướng dẫn", 
            description="Danh sách lệnh của bot:", 
            color=0xBEBEFE
        )
        for i in self.bot.cogs:
            if i == "owner" and not (await self.bot.is_owner(context.author)):
                continue
            cog = self.bot.get_cog(i)
            commands = cog.get_commands()
            data = []
            for command in commands:
                description = command.description
                data.append(f"{prefix}{command.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(
                name=i.capitalize(), value=f"```{help_text}```", inline=False
            )
        await context.send(embed=embed)

    @commands.hybrid_command(name="translate", description="Dịch một đoạn văn bản từ tiếng Anh sang tiếng Việt")
    @app_commands.describe(text= "Văn bản cần dịch")
    async def translate(self, context: Context, *,  text: str) -> None:

        url = "https://google-translator9.p.rapidapi.com/v2"
        querystring = {"q": text, "target": "vi",
                       "source": "en", "format": "text"}

        headers = {
            "X-RapidAPI-Key": "4e43b4c3bcmsh1827e6c7fea3df3p1ed847jsnf9e4737a2128",
            "X-RapidAPI-Host": "google-translator9.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=querystring, headers=headers)
        if response.status_code == 200:
            json_response = response.json()
            if "data" in json_response:
                translated_text = json_response["data"]["translations"][0]["translatedText"]
                await context.send(translated_text)
            else:
                await context.send("Error: 'data' key not found in the response.")
        else:
            await context.send("Lỗi khi dịch văn bản.")

    @commands.hybrid_command(name="weather", description="Thông tin thời tiết của một thành phố")
    @app_commands.describe(city="Tên thành phố cần xem thời tiết")
    async def weather(self, context: Context, *, city: str) -> None:
        url = "https://weather-api167.p.rapidapi.com/api/weather/forecast"
        querystring = {"place": city}

        headers = {
            "x-rapidapi-key": "4e43b4c3bcmsh1827e6c7fea3df3p1ed847jsnf9e4737a2128",
            "x-rapidapi-host": "weather-api167.p.rapidapi.com",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            json_response = response.json()
            embed = weather_embed(json_response)
            await context.send(embed=embed)
        else:
            await context.send("Lỗi khi lấy dữ liệu thời tiết.")

    @commands.hybrid_command(name="wiki", description="Tìm kiếm thông tin trên Wikipedia")
    @app_commands.describe(keyword="Từ khoá cần tìm kiếm")
    async def wiki(self, context: Context, *, keyword: str) -> None:
        url = "https://google.serper.dev/search"

        payload = json.dumps({
            "q": keyword,
            "hl": "vi"
        })
        headers = {
            'X-API-KEY': 'a529bf83ea927359532ebdfab99d2c4de8724c2e',
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
       
        if response.status_code == 200:
            json_response = response.json()
            embed = wiki_embed(json_response)
            await context.send(embed=embed)
        else:
            await context.send("Lỗi khi tìm kiếm thông tin.")

# And then we finally add the cog to the bot
async def setup(bot) -> None:
    await bot.add_cog(Utility(bot))
