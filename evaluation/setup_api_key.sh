#!/bin/bash
# 快速设置 Ragas 评估所需的 OpenAI API Key

echo "🔑 设置 Ragas 评估所需的 OpenAI API Key"
echo "============================================"
echo ""
echo "💡 Ragas 需要 OpenAI API 来评估答案质量（作为评判者）"
echo ""
echo "请选择设置方式："
echo "  1. 输入新的 OpenAI API Key"
echo "  2. 使用现有的 LLM_OPENAI_API_KEY"
echo "  3. 临时设置（本次会话）"
echo ""
read -p "请输入选项 (1/2/3): " choice

case $choice in
  1)
    read -p "请输入 OpenAI API Key: " api_key
    if grep -q "^OPENAI_API_KEY=" .env 2>/dev/null; then
      # 更新现有的
      sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$api_key|" .env
      echo "✅ 已更新 .env 文件中的 OPENAI_API_KEY"
    else
      # 添加新的
      echo "OPENAI_API_KEY=$api_key" >> .env
      echo "✅ 已添加 OPENAI_API_KEY 到 .env 文件"
    fi
    ;;
  2)
    if [ -f .env ]; then
      existing_key=$(grep "^LLM_OPENAI_API_KEY=" .env | cut -d '=' -f2)
      if [ -n "$existing_key" ]; then
        if grep -q "^OPENAI_API_KEY=" .env; then
          sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$existing_key|" .env
        else
          echo "OPENAI_API_KEY=$existing_key" >> .env
        fi
        echo "✅ 已使用 LLM_OPENAI_API_KEY 的值"
        echo "   Key: ${existing_key:0:10}...${existing_key: -4}"
      else
        echo "❌ 未在 .env 中找到 LLM_OPENAI_API_KEY"
        exit 1
      fi
    else
      echo "❌ .env 文件不存在"
      exit 1
    fi
    ;;
  3)
    read -p "请输入 OpenAI API Key: " api_key
    export OPENAI_API_KEY="$api_key"
    echo "✅ 已临时设置 OPENAI_API_KEY（仅本次会话有效）"
    echo ""
    echo "⚠️  注意：关闭终端后需要重新设置"
    echo ""
    echo "运行评估："
    echo "  ./evaluation/run_evaluation.sh"
    ;;
  *)
    echo "❌ 无效选项"
    exit 1
    ;;
esac

echo ""
echo "🎉 设置完成！现在可以运行评估了："
echo "   ./evaluation/run_evaluation.sh"
