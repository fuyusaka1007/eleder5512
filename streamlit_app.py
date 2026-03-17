import streamlit as st
import openai
import time
import base64
import json
import re

# =================配置区域 (从 secrets.toml 读取)=================
# 检查 secrets 是否配置正确
if "qwen" not in st.secrets:
    st.error("❌ 配置错误：未在 .streamlit/secrets.toml 中找到 [qwen] 配置项。")
    st.stop()

# 读取密钥和模型名称
API_KEY = st.secrets["qwen"]["api_key"]
MODEL_NAME = st.secrets["qwen"].get("model_name", "qwen-max") # 默认 fallback 到 qwen-max

# 初始化 Qwen 客户端 (兼容 OpenAI 协议)
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# =================适老化样式 CSS=================
st.markdown("""
<style>
    /* 全局大字体 */
    html, body, [class*="css"] {
        font-size: 24px !important;
        font-family: 'Microsoft YaHei', 'SimSun', sans-serif;
    }
    
    /* 聊天消息气泡放大 */
    .stChatMessage {
        font-size: 26px !important;
        padding: 25px !important;
        border-radius: 20px !important;
        margin-bottom: 15px !important;
    }
    
    /* 输入框放大 */
    .stTextInput > div > div > input {
        font-size: 28px !important;
        height: 70px !important;
        padding: 10px !important;
    }
    
    /* 按钮放大 */
    .stButton > button {
        font-size: 26px !important;
        padding: 20px 40px !important;
        height: auto !important;
        background-color: #FFA500; /* 更明亮的橙色 */
        color: white !important;
        border-radius: 15px !important;
        border: none !important;
        margin: 10px;
    }
    
    /* 隐藏默认菜单和页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 标题样式 */
    h1 {
        font-size: 40px !important;
        color: #D2691E; /* 巧克力色 */
        text-align: center;
        margin-top: 0;
    }

    /* 卡片容器 */
    .card {
        background-color: #FFF8DC; /* Cornsilk 白色背景 */
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    /* 欢迎文字 */
    .welcome-text {
        font-size: 28px;
        text-align: center;
        color: #2F4F4F; /* 深石板灰 */
        margin-bottom: 20px;
    }
    
</style>
""", unsafe_allow_html=True)

# =================初始化 Session State=================
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 初始化系统提示词，设定 Qwen 的角色
    st.session_state.messages.append({
        "role": "system",
        "content": """你叫“暖忆”，是一位专门陪伴老年人的智能助手。
        你的性格：极度耐心、温和、语速慢（文字简短）、充满鼓励。
        当前任务：陪老人玩“对对联”游戏，帮助预防认知衰退。
        
        游戏规则：
        1. 每次只出一个上联，难度要从非常简单（3-5个字）开始，根据老人表现慢慢增加难度。
        2. 如果老人对出来了，要大力表扬，并解释一下对联的妙处，然后出下一个。
        3. 如果老人对不出来或答错了，千万不要批评。要先肯定他的尝试，然后给一点提示（比如提示第一个字，或者解释上联的意思），引导他再试一次。
        4. 如果老人连续两次答不出，直接公布下联，并简单讲解，然后换一个更简单的题目。
        5. 回复要简短，避免长篇大论，方便老人阅读。
        6. 始终使用尊称“您”。
        
        当前状态：游戏刚开始，请先热情地打招呼，并出一个最简单的三字或四字上联。
        """
    })

# =================工具函数=================
def get_qwen_response(messages):
    """调用 Qwen API via OpenAI compatible endpoint"""
    try:
        response = client.chat.completions.create(
            model='qwen-max', # 或者 qwen-turbo, qwen-plus
            messages=messages,
            stream=False, # 禁用流式输出，一次性获取完整回复
            temperature=0.7, # 稍微有点创造性，但保持稳健
            max_tokens=200, # 控制输出长度
        )
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"AI服务暂时不可用，请稍后再试。错误信息: {str(e)}")
        return "暖忆暂时无法回应您，可能是因为网络有点忙，请稍后再试哦。"

# =================主界面逻辑=================
# 主标题
st.markdown('<h1>🏮 暖忆 · 快乐对对联 🏮</h1>', unsafe_allow_html=True)

# 欢迎卡片
st.markdown('<div class="card"><p class="welcome-text">您好，我是暖忆！<br>让我们一起动动脑筋，开心地对对联吧！</p></div>', unsafe_allow_html=True)

# 展示聊天历史
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    avatar = "👴" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 输入区域
if prompt := st.chat_input("请输入您的下联，或点击下方按钮寻求帮助..."):
    # 添加用户消息到历史记录
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👴"):
        st.markdown(prompt)

    # 生成并显示 AI 回复
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        # 临时显示加载动画
        message_placeholder.markdown("...")
        full_response = get_qwen_response(st.session_state.messages)
        message_placeholder.markdown(full_response)
    
    # 添加 AI 消息到历史记录
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# =================辅助功能按钮区域=================
st.markdown('---')
st.markdown('<p style="text-align: center; font-size: 26px;">需要帮助吗？</p>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("💡 给我提示"):
        hint_msg = {"role": "user", "content": "这个上联有点难，能给我一点点提示吗？"}
        st.session_state.messages.append(hint_msg)
        with st.chat_message("user", avatar="👴"):
            st.markdown(hint_msg["content"])
        
        with st.chat_message("assistant", avatar="🤖"):
            resp = get_qwen_response(st.session_state.messages)
            st.markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})

with col2:
    if st.button("🔄 换个简单的"):
        simple_msg = {"role": "user", "content": "换个特别简单的对联吧，让我试试。"}
        st.session_state.messages.append(simple_msg)
        with st.chat_message("user", avatar="👴"):
            st.markdown(simple_msg["content"])
        
        with st.chat_message("assistant", avatar="🤖"):
            resp = get_qwen_response(st.session_state.messages)
            st.markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})

with col3:
    if st.button("👋 结束对话"):
        st.session_state.messages.append({"role": "assistant", "content": "今天和您对对联真开心！记得多动动脑筋哦，暖忆下次再来陪您！"})
        st.balloons()
        st.info("感谢您的使用！您可以刷新页面重新开始。")

# =================页脚=================
st.markdown('---')
st.markdown('<div style="text-align: center; color: #808080; font-size: 18px;">© 2024 暖忆项目组 | 让陪伴更温暖，让记忆更清晰</div>', unsafe_allow_html=True)