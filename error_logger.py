"""
Error Logger for News GPT v2
에러 이력을 error_history.md 파일에 자동으로 기록하는 시스템
"""

import os
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
import json

class ErrorLogger:
    def __init__(self, log_file_path: str = "error_history.md"):
        self.log_file_path = log_file_path
        self.ensure_log_file_exists()
    
    def ensure_log_file_exists(self):
        """로그 파일이 없으면 기본 템플릿으로 생성"""
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write("# 🚨 Error History - News GPT v2\n\n")
    
    def log_error(self, 
                  error: Exception, 
                  file_name: Optional[str] = None,
                  function_name: Optional[str] = None,
                  context: Optional[str] = None,
                  additional_info: Optional[Dict[str, Any]] = None,
                  severity: str = "HIGH") -> None:
        """
        에러를 로그 파일에 기록
        
        Args:
            error: 발생한 예외 객체
            file_name: 에러 발생 파일명
            function_name: 에러 발생 함수명
            context: 에러 발생 상황 설명
            additional_info: 추가 정보 (딕셔너리)
            severity: 에러 심각도 (HIGH, MEDIUM, LOW)
        """
        try:
            # 현재 시간
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            # 에러 타입 및 메시지
            error_type = type(error).__name__
            error_message = str(error)
            
            # 자동으로 파일명과 함수명 추출 (제공되지 않은 경우)
            if not file_name or not function_name:
                tb = traceback.extract_tb(error.__traceback__)
                if tb:
                    # 가장 최근 호출 스택에서 정보 추출
                    last_frame = tb[-1]
                    file_name = file_name or os.path.basename(last_frame.filename)
                    function_name = function_name or last_frame.name
            
            # 심각도 이모지
            severity_emoji = {
                "HIGH": "🔴",
                "MEDIUM": "🟡", 
                "LOW": "🟢"
            }
            emoji = severity_emoji.get(severity, "🔴")
            
            # 에러 로그 엔트리 생성
            log_entry = self._create_log_entry(
                date_str, time_str, error_type, error_message,
                file_name, function_name, context, additional_info, 
                emoji, severity
            )
            
            # 파일에 추가
            self._append_to_log_file(log_entry)
            
            # 통계 업데이트
            self._update_statistics()
            
            print(f"🔴 에러가 error_history.md에 기록되었습니다: {error_type}")
            
        except Exception as log_error:
            print(f"❌ 에러 로깅 중 오류 발생: {log_error}")
    
    def _create_log_entry(self, date_str: str, time_str: str, error_type: str, 
                         error_message: str, file_name: Optional[str], function_name: Optional[str],
                         context: Optional[str], additional_info: Optional[Dict[str, Any]], 
                         emoji: str, severity: str) -> str:
        """로그 엔트리 텍스트 생성"""
        
        entry = f"""
## {emoji} [{date_str}] [{time_str}] - {error_type}
- **파일**: {file_name or 'Unknown'}
- **함수**: {function_name or 'Unknown'}
- **심각도**: {severity}
- **에러 메시지**: `{error_message}`
- **상황**: {context or '상황 정보 없음'}
- **스택 트레이스**: 
```
{traceback.format_exc()}
```
"""
        
        if additional_info:
            entry += f"- **추가 정보**: \n```json\n{json.dumps(additional_info, indent=2, ensure_ascii=False)}\n```\n"
        
        entry += "- **해결방안**: 미해결\n"
        entry += "- **상태**: 🔴 미해결\n"
        entry += "\n---\n"
        
        return entry
    
    def _append_to_log_file(self, log_entry: str):
        """로그 파일에 엔트리 추가"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 오늘 날짜 섹션 찾기
            today = datetime.now().strftime("%Y-%m-%d")
            today_section = f"### {today}"
            
            if today_section in content:
                # 오늘 날짜 섹션이 있으면 그 아래에 추가
                insert_pos = content.find(today_section)
                next_section = content.find("### ", insert_pos + 1)
                if next_section == -1:
                    next_section = content.find("---", insert_pos)
                
                if next_section != -1:
                    new_content = content[:next_section] + log_entry + "\n" + content[next_section:]
                else:
                    new_content = content + log_entry
            else:
                # 오늘 날짜 섹션이 없으면 새로 생성
                history_start = content.find("## 🔍 에러 이력")
                if history_start != -1:
                    section_start = content.find("\n", history_start) + 1
                    new_section = f"\n### {today} ({self._get_weekday()})\n{log_entry}"
                    new_content = content[:section_start] + new_section + content[section_start:]
                else:
                    new_content = content + f"\n### {today} ({self._get_weekday()})\n{log_entry}"
            
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
        except Exception as e:
            print(f"❌ 로그 파일 작성 오류: {e}")
    
    def _get_weekday(self) -> str:
        """요일 반환 (한국어)"""
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        return weekdays[datetime.now().weekday()]
    
    def _update_statistics(self):
        """에러 통계 업데이트"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 에러 개수 계산
            total_errors = content.count("## 🔴") + content.count("## 🟡") + content.count("## 🟢")
            resolved_errors = content.count("🟢 해결완료")
            unresolved_errors = total_errors - resolved_errors
            
            # 통계 섹션 업데이트
            stats_section = "## 📊 에러 통계"
            stats_start = content.find(stats_section)
            if stats_start != -1:
                stats_end = content.find("---", stats_start)
                if stats_end != -1:
                    new_stats = f"""## 📊 에러 통계

- **총 에러 수**: {total_errors}개
- **해결된 에러**: {resolved_errors}개
- **미해결 에러**: {unresolved_errors}개
- **마지막 업데이트**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
                    new_content = content[:stats_start] + new_stats + content[stats_end:]
                    
                    with open(self.log_file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                        
        except Exception as e:
            print(f"❌ 통계 업데이트 오류: {e}")
    
    def mark_resolved(self, error_date: str, error_time: str, solution: str):
        """특정 에러를 해결됨으로 표시"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 해당 에러 찾기
            error_marker = f"[{error_date}] [{error_time}]"
            error_pos = content.find(error_marker)
            
            if error_pos != -1:
                # 해결방안 업데이트
                solution_pos = content.find("- **해결방안**: 미해결", error_pos)
                if solution_pos != -1:
                    new_content = content.replace(
                        "- **해결방안**: 미해결",
                        f"- **해결방안**: {solution}",
                        1
                    )
                    new_content = new_content.replace(
                        "- **상태**: 🔴 미해결",
                        "- **상태**: 🟢 해결완료",
                        1
                    )
                    
                    with open(self.log_file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"✅ 에러가 해결됨으로 표시되었습니다: {error_marker}")
                    self._update_statistics()
                    
        except Exception as e:
            print(f"❌ 에러 상태 업데이트 오류: {e}")

# 글로벌 에러 로거 인스턴스
error_logger = ErrorLogger()

def log_error(error: Exception, 
              file_name: Optional[str] = None,
              function_name: Optional[str] = None,
              context: Optional[str] = None,
              additional_info: Optional[Dict[str, Any]] = None,
              severity: str = "HIGH"):
    """편의 함수: 에러 로깅"""
    error_logger.log_error(error, file_name, function_name, context, additional_info, severity)

def mark_error_resolved(error_date: str, error_time: str, solution: str):
    """편의 함수: 에러 해결됨 표시"""
    error_logger.mark_resolved(error_date, error_time, solution)

# 데코레이터: 함수의 예외를 자동으로 로깅
def auto_log_errors(severity: str = "HIGH"):
    """데코레이터: 함수에서 발생하는 예외를 자동으로 로깅"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(
                    error=e,
                    file_name=func.__module__.split('.')[-1] + ".py",
                    function_name=func.__name__,
                    context=f"함수 {func.__name__} 실행 중 에러 발생",
                    additional_info={
                        "args": str(args) if args else None,
                        "kwargs": str(kwargs) if kwargs else None
                    },
                    severity=severity
                )
                raise  # 원래 예외를 다시 발생시킴
        return wrapper
    return decorator

if __name__ == "__main__":
    # 테스트 예제
    try:
        raise ValueError("테스트 에러입니다")
    except Exception as e:
        log_error(
            error=e,
            file_name="test.py",
            function_name="test_function",
            context="에러 로깅 시스템 테스트",
            additional_info={"test": True},
            severity="LOW"
        )
