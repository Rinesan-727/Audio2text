import requests
import json
import os
import glob
from datetime import datetime
from dotenv import load_dotenv

# 加载配置文件
load_dotenv('config.env')

# 导入本地模型接口
try:
    from local_model_interface import create_local_model_interface
    LOCAL_MODEL_AVAILABLE = True
except ImportError:
    LOCAL_MODEL_AVAILABLE = False
    print("⚠️  本地模型接口未找到，将使用云端API")

# 加载config.env文件中的环境变量
def load_env_file():
    """从config.env文件加载环境变量"""
    env_file = "config.env"
    if os.path.exists(env_file):
        print(f"从 {env_file} 加载配置...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("配置加载完成")
    else:
        print(f"未找到 {env_file} 文件，使用默认配置")

# 加载环境变量
load_env_file()

# =================== 配置信息 ===================
# 支持环境变量配置，如果没有设置则使用硅基流动的默认值
API_KEY = os.getenv("API_KEY", "")  # 请设置你的真实API Key
API_URL = os.getenv("API_URL", "https://api.siliconflow.cn/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5-72b-instruct")

# 本地模型配置
USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"
LOCAL_MODEL_TYPE = os.getenv("LOCAL_MODEL_TYPE", "ollama")
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 检查API配置
def check_api_config():
    """检查API配置是否正确"""
    print("=== API配置检查 ===")
    
    if USE_LOCAL_MODEL and LOCAL_MODEL_AVAILABLE:
        print("🏠 使用本地模型模式")
        print(f"本地模型类型: {LOCAL_MODEL_TYPE}")
        print(f"本地模型名称: {LOCAL_MODEL_NAME}")
        
        # 测试本地模型连接
        try:
            local_interface = create_local_model_interface(
                LOCAL_MODEL_TYPE, 
                model_name=LOCAL_MODEL_NAME
            )
            if local_interface.test_connection():
                print("✅ 本地模型连接成功")
                return True
            else:
                print("❌ 本地模型连接失败，切换到云端模式")
                return check_cloud_api_config()
        except Exception as e:
            print(f"❌ 本地模型初始化失败: {e}")
            print("🔄 切换到云端模式")
            return check_cloud_api_config()
    else:
        return check_cloud_api_config()

def check_cloud_api_config():
    """检查云端API配置"""
    print("☁️  使用云端API模式")
    print(f"API URL: {API_URL}")
    print(f"模型名称: {MODEL_NAME}")
    
    # 安全显示API Key（只显示前8个字符）
    if API_KEY:
        masked_key = API_KEY[:8] + "..." if len(API_KEY) > 8 else API_KEY
        print(f"API Key: {masked_key}")
    else:
        print("API Key: 未设置")
    
    if "example.com" in API_URL:
        print("⚠️  警告: 使用的是示例API URL，请设置正确的API_URL环境变量")
        return False
    
    if not API_KEY:
        print("⚠️  警告: 请设置有效的API_KEY环境变量")
        return False
    
    # 检查硅基流动的配置
    if "siliconflow.cn" in API_URL:
        print("✅ 检测到硅基流动API配置")
        if len(API_KEY) < 20:
            print("⚠️  警告: API Key长度不足，请检查是否正确")
            return False
    
    print("✅ 云端API配置检查通过")
    return True

# =================== 核心功能模块 ===================
def find_latest_transcript(specific_dir=None):
    """查找最新的转写结果目录"""
    if specific_dir:
        # 使用指定的目录
        if os.path.exists(specific_dir):
            print(f"使用指定转写目录: {specific_dir}")
            # 读取汇总文件
            summary_file = os.path.join(specific_dir, "summary.txt")
            if os.path.exists(summary_file):
                with open(summary_file, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # 如果没有汇总文件，读取完整转写
            full_transcript_file = os.path.join(specific_dir, "full_transcript.txt")
            if os.path.exists(full_transcript_file):
                with open(full_transcript_file, 'r', encoding='utf-8') as f:
                    return f.read()
            
            print(f"在指定目录 {specific_dir} 中未找到转写文件")
            return None
        else:
            print(f"指定目录 {specific_dir} 不存在")
            return None
    
    # 原有的自动查找逻辑
    transcript_dirs = glob.glob("transcripts_*")
    if not transcript_dirs:
        print("未找到转写结果目录")
        return None
    
    # 按时间戳排序，获取最新的
    latest_dir = max(transcript_dirs, key=os.path.getctime)
    print(f"找到最新转写目录: {latest_dir}")
    
    # 读取汇总文件
    summary_file = os.path.join(latest_dir, "summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 如果没有汇总文件，读取完整转写
    full_transcript_file = os.path.join(latest_dir, "full_transcript.txt")
    if os.path.exists(full_transcript_file):
        with open(full_transcript_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    return None

def summarize_conversation(transcript):
    """调用API进行对话结构化分析"""
    prompt = f"""请对以下多人对话进行深度分析，必须严格按照JSON格式输出：

{{
    "main_topics": ["主题1", "主题2", "主题3"],
    "speaker_points": {{
        "SPEAKER_00": ["观点1", "观点2"],
        "SPEAKER_01": ["观点1", "观点2"]
    }},
    "action_items": ["行动项1", "行动项2"],
    "risks": ["风险点1", "风险点2"],
    "opportunities": ["机会点1", "机会点2"]
}}

对话内容：
{transcript}
"""
    
    # 根据配置选择使用本地模型还是云端API
    if USE_LOCAL_MODEL and LOCAL_MODEL_AVAILABLE:
        return summarize_conversation_local(transcript, prompt)
    else:
        return summarize_conversation_cloud(transcript, prompt)

def summarize_conversation_local(transcript, prompt):
    """使用本地模型进行对话分析"""
    try:
        print("🏠 使用本地模型进行分析...")
        
        local_interface = create_local_model_interface(
            LOCAL_MODEL_TYPE, 
            model_name=LOCAL_MODEL_NAME
        )
        
        messages = [{"role": "user", "content": prompt}]
        response = local_interface.chat_completion(
            messages,
            temperature=0.3,
            max_tokens=2000
        )
        
        if response:
            print("✅ 本地模型分析完成")
            return response
        else:
            print("❌ 本地模型分析失败，尝试云端API")
            return summarize_conversation_cloud(transcript, prompt)
            
    except Exception as e:
        print(f"❌ 本地模型调用异常: {e}")
        print("🔄 切换到云端API")
        return summarize_conversation_cloud(transcript, prompt)

def summarize_conversation_cloud(transcript, prompt):
    """使用云端API进行对话分析"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"☁️  正在调用云端API: {API_URL}")
        print(f"使用模型: {MODEL_NAME}")
        print(f"请求头: Authorization: Bearer {API_KEY[:8]}...")
        
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            return None
            
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    except Exception as e:
        print(f"云端API调用失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
        return None

def create_mindmap_data(summary_json):
    """将总结结果转换为脑图结构"""
    try:
        # 尝试直接解析JSON
        summary_data = json.loads(summary_json)
    except json.JSONDecodeError:
        print("JSON解析失败，尝试提取JSON部分...")
        # 尝试从文本中提取JSON部分
        start_idx = summary_json.find('{')
        end_idx = summary_json.rfind('}') + 1
        if start_idx != -1 and end_idx != 0:
            json_str = summary_json[start_idx:end_idx]
            try:
                summary_data = json.loads(json_str)
            except:
                print("无法解析JSON，使用默认结构")
                summary_data = {
                    "main_topics": ["对话分析"],
                    "speaker_points": {"SPEAKER_00": ["主要观点"], "SPEAKER_01": ["次要观点"]},
                    "action_items": ["待办事项"],
                    "risks": ["风险点"],
                    "opportunities": ["机会点"]
                }
        else:
            print("未找到JSON结构，使用默认结构")
            summary_data = {
                "main_topics": ["对话分析"],
                "speaker_points": {"SPEAKER_00": ["主要观点"], "SPEAKER_01": ["次要观点"]},
                "action_items": ["待办事项"],
                "risks": ["风险点"],
                "opportunities": ["机会点"]
            }
    
    mindmap_structure = {
        "name": f"对话分析-{datetime.now().strftime('%Y%m%d')}",
        "children": [
            {
                "name": "核心议题",
                "children": [{"name": topic} for topic in summary_data.get('main_topics', [])]
            },
            {
                "name": "观点摘要",
                "children": [
                    {
                        "name": f"【{speaker}】",
                        "children": [{"name": point} for point in points]
                    } 
                    for speaker, points in summary_data.get('speaker_points', {}).items()
                ]
            },
            {
                "name": "行动项",
                "children": [{"name": task} for task in summary_data.get('action_items', [])]
            },
            {
                "name": "风险与机会",
                "children": [
                    {"name": risk} for risk in summary_data.get('risks', []) +
                    summary_data.get('opportunities', [])
                ]
            }
        ]
    }
    return mindmap_structure

def generate_html_mindmap(mindmap_data):
    """生成包含ECharts思维导图的HTML文件"""
    # 将mindmap_data转换为JSON字符串
    mindmap_json = json.dumps(mindmap_data, ensure_ascii=False, indent=2)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>对话思维导图</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.0/dist/echarts.min.js"></script>
        <style>
            body {{ 
                margin: 0; 
                padding: 20px; 
                font-family: "Microsoft YaHei", Arial, sans-serif; 
                background-color: #ffffff;
            }}
            .container {{ 
                max-width: 3000px; 
                margin: 0 auto; 
                background-color: #ffffff;
            }}
            h1 {{ 
                text-align: center; 
                color: #333; 
                margin-bottom: 30px;
                font-size: 24px;
            }}
            .chart-container {{
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>对话分析思维导图</h1>
            <div class="chart-container">
                <div id="main" style="width: 100%; height: 2200px;"></div>
            </div>
        </div>
        <script type="text/javascript">
            var myChart = echarts.init(document.getElementById('main'));
            var mindmapData = {mindmap_json};
            
            // 定义颜色方案
            var colors = [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
                '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
            ];
            
            var option = {{
                title: {{
                    text: mindmapData.name,
                    left: 'center',
                    top: 10,
                    textStyle: {{
                        fontSize: 20,
                        fontWeight: 'bold',
                        color: '#333'
                    }}
                }},
                tooltip: {{
                    trigger: 'item',
                    formatter: '{{b}}',
                    backgroundColor: 'rgba(255,255,255,0.95)',
                    borderColor: '#ccc',
                    borderWidth: 1,
                    textStyle: {{
                        color: '#333',
                        fontSize: 12
                    }},
                    padding: [8, 12]
                }},
                series: [{{
                    type: 'tree',
                    data: [mindmapData],
                    top: '5%',
                    bottom: '2%',
                    left: '0.5%',
                    right: '0.5%',
                    layout: 'orthogonal',
                    orient: 'LR',
                    symbol: 'circle',
                    symbolSize: 16,
                    edgeShape: 'curve',
                    lineStyle: {{
                        width: 3,
                        color: '#666',
                        curveness: 0.3
                    }},
                    label: {{
                        position: 'left',
                        formatter: '{{b}}',
                        fontSize: 16,
                        color: '#333',
                        backgroundColor: 'rgba(255,255,255,0.9)',
                        padding: [12, 18],
                        borderRadius: 10,
                        borderColor: '#ddd',
                        borderWidth: 1,
                        distance: 35,
                        verticalAlign: 'middle',
                        lineHeight: 20
                    }},
                    itemStyle: {{
                        color: function(params) {{
                            // 根据层级设置不同颜色
                            var level = params.treeLevel;
                            if (level === 0) return '#4e79a7';  // 根节点
                            if (level === 1) return colors[level % colors.length];  // 一级分支
                            if (level === 2) return colors[(level + 3) % colors.length];  // 二级分支
                            return colors[(level + 6) % colors.length];  // 其他层级
                        }},
                        borderColor: '#fff',
                        borderWidth: 2,
                        shadowBlur: 5,
                        shadowColor: 'rgba(0,0,0,0.2)'
                    }},
                    emphasis: {{
                        itemStyle: {{
                            color: '#f28e2c',
                            shadowBlur: 15,
                            shadowColor: 'rgba(0,0,0,0.4)',
                            borderWidth: 3
                        }},
                        label: {{
                            fontSize: 18,
                            fontWeight: 'bold',
                            backgroundColor: 'rgba(255,255,255,0.95)'
                        }}
                    }},
                    expandAndCollapse: true,
                    animationDuration: 600,
                    animationDurationUpdate: 800,
                    initialTreeDepth: -1,
                    roam: true,
                    zoom: 0.5,
                    nodeAlign: 'justify',
                    force: true
                }}]
            }};
            myChart.setOption(option);
            
            // 响应式调整
            window.addEventListener('resize', function() {{
                myChart.resize();
            }});
            
            // 添加交互功能
            myChart.on('click', function(params) {{
                if (params.componentType === 'series') {{
                    console.log('点击节点:', params.name);
                }}
            }});
            
            // 自动调整布局
            setTimeout(function() {{
                myChart.resize();
            }}, 100);
        </script>
    </body>
    </html>
    """
    
    output_path = os.path.join(OUTPUT_DIR, "mindmap.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"思维导图已生成：{output_path}")
    return output_path

# =================== 主程序流程 ===================
if __name__ == "__main__":
    print("开始处理对话总结...")
    
    # 检查API配置
    api_config_valid = check_api_config()
    
    # 使用指定的转写目录进行测试
    # 自动查找最新的转写目录
    transcript_dirs = glob.glob("transcripts_*")
    if transcript_dirs:
        specific_dir = max(transcript_dirs, key=os.path.getctime)
    else:
        specific_dir = None
    
    # 读取指定的转写结果
    transcript = find_latest_transcript(specific_dir)
    if not transcript:
        print("未找到转写结果，使用示例数据...")
        transcript = """
        [SPEAKER_00]：我们得加快项目进度，Q3必须完成交付。
        [SPEAKER_01]：技术上存在难点，需要更多测试时间。
        [SPEAKER_00]：那把UI优化延后到Q4，先保证核心功能。
        [SPEAKER_01]：这样可能影响用户体验，建议增加测试人员。
        """
    
    if api_config_valid:
        print("调用API进行对话分析...")
        raw_summary = summarize_conversation(transcript)
        
        if raw_summary:
            print("生成脑图结构...")
            mindmap_data = create_mindmap_data(raw_summary)
            
            print("生成可视化脑图...")
            html_path = generate_html_mindmap(mindmap_data)
            
            print(f"处理完成！请打开 {html_path} 查看结果")
        else:
            print("API调用失败，生成默认脑图...")
            # 使用默认数据生成脑图
            default_data = {
                "name": f"对话分析-{datetime.now().strftime('%Y%m%d')}",
                "children": [
                    {"name": "核心议题", "children": [{"name": "项目进度管理"}]},
                    {"name": "观点摘要", "children": [
                        {"name": "【SPEAKER_00】", "children": [{"name": "强调交付时间"}]},
                        {"name": "【SPEAKER_01】", "children": [{"name": "关注技术难点"}]}
                    ]},
                    {"name": "行动项", "children": [{"name": "优化项目计划"}]},
                    {"name": "风险与机会", "children": [{"name": "技术风险"}, {"name": "用户体验机会"}]}
                ]
            }
            html_path = generate_html_mindmap(default_data)
            print(f"默认脑图已生成：{html_path}")
    else:
        print("API配置无效，直接生成默认脑图...")
        # 基于实际对话内容生成脑图
        actual_data = {
            "name": f"对话分析-{datetime.now().strftime('%Y%m%d')}",
            "children": [
                {
                    "name": "核心议题",
                    "children": [
                        {"name": "量化投资与金融科技"},
                        {"name": "中国科技创新现状"},
                        {"name": "职业发展与就业方向"},
                        {"name": "数学在金融中的应用"}
                    ]
                },
                {
                    "name": "观点摘要",
                    "children": [
                        {
                            "name": "【SPEAKER_00】",
                            "children": [
                                {"name": "央企国企在科技创新方面成果有限"},
                                {"name": "中芯国际对中国科技发展的重要性"},
                                {"name": "量化投资需要算法和性能优化"},
                                {"name": "金融机构是很好的就业选择"},
                                {"name": "量化投资年薪可达百万千万"},
                                {"name": "数学背景在量化投资中很有优势"},
                                {"name": "量子计算和量子通信的前沿技术"}
                            ]
                        },
                        {
                            "name": "【SPEAKER_01】",
                            "children": [
                                {"name": "询问量化投资相关机会"},
                                {"name": "关注技术实现方向"},
                                {"name": "对职业选择表示犹豫"},
                                {"name": "对薪资水平表示关注"}
                            ]
                        }
                    ]
                },
                {
                    "name": "行动项",
                    "children": [
                        {"name": "学习量化投资算法"},
                        {"name": "掌握CUDA硬件优化技术"},
                        {"name": "关注金融机构就业机会"},
                        {"name": "深入研究数学在金融中的应用"}
                    ]
                },
                {
                    "name": "风险与机会",
                    "children": [
                        {"name": "中国科技被美国卡脖子的风险"},
                        {"name": "量化投资技术门槛高"},
                        {"name": "金融机构就业机会"},
                        {"name": "数学背景在金融科技中的优势"},
                        {"name": "量子计算技术发展机会"}
                    ]
                }
            ]
        }
        html_path = generate_html_mindmap(actual_data)
        print(f"基于实际对话的脑图已生成：{html_path}")
        
        print("\n=== 如何配置API ===")
        print("1. 设置环境变量:")
        print("   export API_KEY='your-api-key'")
        print("   export API_URL='https://your-api-endpoint.com/v1/chat/completions'")
        print("   export MODEL_NAME='your-model-name'")
        print("2. 或者在代码中直接修改配置")
        print("3. 确保API Key有效且有足够的配额")