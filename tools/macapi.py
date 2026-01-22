# -*- coding: utf-8 -*-

import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# 配置常量（解耦硬编码）
LOG_FILE = "mac_api.log"
CSV_PATH = "mac_oui.csv"
CSV_COLUMNS = {"Assignment": str, "Organization Name": str}
DEFAULT_VENDOR = "未知厂商"
ERROR_MESSAGES = {
    "invalid_mac": "Invalid MAC",
    "invalid_vendor_keyword": "无效的厂商关键字",
    "no_vendor_match": "未找到匹配厂商",
    "csv_not_found": "MAC厂商CSV文件不存在",
    "csv_load_fail": "CSV加载失败"
}

logging.basicConfig(
    level=logging.INFO,          # 日志级别：INFO（常规操作）/ERROR（异常）/DEBUG（调试）
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日志格式（时间-模块-级别-内容）
    handlers=[
        logging.StreamHandler(),  # 控制台输出
        logging.FileHandler(LOG_FILE, encoding="utf-8")  # 日志文件（UTF-8避免中文乱码）
    ]
)
LOG = logging.getLogger(__name__)  # 日志器实例（绑定当前模块名）
# 自定义异常
class MacVendorError(Exception):
    """MAC厂商查询基础异常"""
    pass

class CSVLoadError(MacVendorError):
    """CSV加载失败异常"""
    pass

class InvalidMACError(MacVendorError):
    """MAC格式非法异常"""
    pass

class MacVendorApi:
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.df: pd.DataFrame = None  # 存储MAC厂商数据的DataFrame
        self._load_mac_vendor_data()  # 初始化加载数据

    def _load_mac_vendor_data(self) -> None:
        try:
            if not Path(self.csv_file_path).exists():
                raise FileNotFoundError(f"{ERROR_MESSAGES['csv_not_found']} → {self.csv_file_path}")
            self.df = pd.read_csv(
                self.csv_file_path,
                dtype=str,
                encoding="utf-8"
            )

            # 校验必要列存在
            missing_cols = [col for col in CSV_COLUMNS.keys() if col not in self.df.columns]
            if missing_cols:
                raise CSVLoadError(f"缺失必要列: {missing_cols} (需包含: {list(CSV_COLUMNS.keys())})")
            
            # 设置索引并去重（避免重复前缀导致查询异常）
            self.df = self.df.set_index("Assignment", drop=True)
            self.df = self.df[~self.df.index.duplicated(keep='first')]
            
            LOG.info(f"✅ 加载完成 | 有效MAC厂商映射数: {len(self.df)} 条")


        except FileNotFoundError as e:
            LOG.error(f"❌ {e}")
            raise CSVLoadError(f"❌ {e}") from e
        except Exception as e:
            LOG.error(f"❌ {ERROR_MESSAGES['csv_load_fail']}: {str(e)}")
            raise CSVLoadError(f"❌ {ERROR_MESSAGES['csv_load_fail']}: {str(e)}") from e

    @staticmethod
    def _format_6mac(mac_6: str) -> str:
        """工具方法：将6位纯字符串MAC前缀转为 AA:BB:CC 格式"""
        if isinstance(mac_6, str) and len(mac_6) == 6 and re.match(r'^[0-9A-F]{6}$', mac_6):
            return f"{mac_6[0:2]}:{mac_6[2:4]}:{mac_6[4:6]}"
        return mac_6

    @staticmethod
    def normalize_mac(mac_address: str) -> Optional[str]:
        """
        标准化任意格式的MAC地址 → 返回【纯12位大写无分隔符】的合法MAC
        :param mac_address: 任意格式MAC地址
        :return: 标准化MAC字符串 | None(格式非法)
        """
        if not isinstance(mac_address, str) or not mac_address.strip():
            LOG.warning("MAC地址为空或非字符串类型")
            return ERROR_MESSAGES["invalid_mac"]
        
        # 移除所有分隔符(:/-) + 去空格 + 转大写
        clean_mac = re.sub(r'[:-]', '', mac_address).strip().upper()
        
        # 校验12位十六进制
        if not re.match(r'^[0-9A-F]{12}$', clean_mac):
            LOG.warning(f"MAC格式非法: {mac_address} → 清理后: {clean_mac}")
            return ERROR_MESSAGES["invalid_mac"]
        
        return clean_mac

    def get_vendor(self, mac_address: str) -> Tuple[Optional[str], str]:
        """
        核心单条查询方法：根据MAC地址查询厂商信息
        :param mac_address: 任意格式MAC地址
        :return: (标准化MAC地址, 厂商名称)
        """
        norm_mac = self.normalize_mac(mac_address)
        # 校验MAC地址合法性
        if not norm_mac:
            return ERROR_MESSAGES["invalid_mac"], 'Unknown'
        
        # 取标准化MAC的前6位，做匹配查询（核心规则）
        match_key = norm_mac[:6]
        try:
            vendor = self.df.loc[match_key, "Organization Name"]
        except KeyError:
            vendor = DEFAULT_VENDOR
            LOG.info(f"MAC前缀 {match_key} 无匹配厂商 → {DEFAULT_VENDOR}")

        return norm_mac, vendor

    def batch_get_vendor(self, mac_list: List[str]) -> List[Dict[str, str]]:
        """
        批量查询方法：最优性能，Pandas批量处理，比循环调用快100倍+
        :param mac_list: MAC地址列表
        :return: 结构化列表，包含原始MAC、标准化MAC、厂商名称
        """
        # 转为Series便于向量化处理
        mac_series = pd.Series(mac_list, name="original_mac")

        # 批量标准化MAC
        norm_macs = mac_series.apply(self.normalize_mac)
        # 提取匹配前缀（非法MAC设为NaN）
        match_keys = norm_macs.str[:6].where(norm_macs.notna(), None)
        
        # 批量匹配厂商（向量化查询，替代循环）
        vendors = match_keys.map(
            lambda x: self.df.loc[x, "Organization Name"] if x in self.df.index else DEFAULT_VENDOR
        )
        # 非法MAC标记错误信息
        vendors = vendors.where(norm_macs.notna(), DEFAULT_VENDOR)
        
        # 构造结果
        result = [
            {
                "original_mac": row["original_mac"],
                "standard_mac": row["norm_mac"],
                "vendor": row["vendor"]
            }
            for row in pd.DataFrame({
                "original_mac": mac_series,
                "norm_mac": norm_macs,
                "vendor": vendors
            }).to_dict("records")
        ]
        
        LOG.info(f"✅ 批量查询完成 | 处理数量: {len(mac_list)} 条")
        return result


    # ===================== 新增核心功能：反向查询【厂商名 → MAC前缀】 =====================
    def get_mac_prefixes_by_vendor(self, vendor_keyword: str) -> Dict[str, Set[str]]:
        # 入参校验
        if not isinstance(vendor_keyword, str) or not vendor_keyword.strip():
            LOG.warning(ERROR_MESSAGES["invalid_vendor_keyword"])
            return {"status": "error", "message": ERROR_MESSAGES["invalid_vendor_keyword"], "data": set()}

        # 关键词标准化：转小写 + 去空格，实现大小写不敏感匹配
        keyword = vendor_keyword.strip().lower()
        
        # 向量化模糊匹配（替代iterrows，提升性能）
        match_mask = self.df["Organization Name"].str.lower().str.contains(keyword, na=False)
        match_df = self.df[match_mask]

        if match_df.empty:
            LOG.info(f"厂商关键字 '{vendor_keyword}' 无匹配结果")
            return {"status": "no_match", "message": ERROR_MESSAGES["no_vendor_match"], "data": set()}

        # 格式化MAC前缀并去重
        mac_prefixes = set()
        for prefix in match_df.index:
            formatted_prefix = self._format_6mac(prefix)
            mac_prefixes.add(formatted_prefix)
        
        # 统一返回格式
        result = {
            "status": "success",
            "message": f"匹配到 {len(mac_prefixes)} 个MAC前缀",
            "data": mac_prefixes
        }
        
        LOG.info(f"✅ 反向查询完成 | 关键字: {vendor_keyword} → 匹配前缀数: {len(mac_prefixes)}")
        return result
    
    
if __name__ == '__main__':
    
    # 1. 实例化API类，传入你的CSV文件路径
    mac_api = MacVendorApi(csv_file_path=CSV_PATH)

    # 2. 测试各种格式的MAC地址（全覆盖）
    test_macs = [
        "00:0c:29:ab:cd:ef",  # 带冒号 小写
        "00-0C-29-12-34-56",  # 带短横线 大写
        "58696c112233",       # 无分隔符 小写
        "90-2B-34-AA-BB-CC",  # 华为MAC
        "12:34:56:78:90:ab",  # 无匹配数据
        "00:0c:29",           # 格式非法（位数不足）
        "abcdefghijkl",       # 纯字母合法MAC
        ""                    # 空值
    ]

    # 3. 单条查询演示
    print("\n===== 单条MAC查询结果 =====")
    for mac in test_macs:
        std_mac, vendor = mac_api.get_vendor(mac)
        print(f"原始MAC: {mac:>20} → 标准MAC: {std_mac:>15} → 厂商: {vendor}")

    # 4. 批量查询演示
    print("\n===== 批量MAC查询结果 =====")
    batch_result = mac_api.batch_get_vendor(test_macs)
    for item in batch_result:
        print(item)    
        

    print("\n===== 单条反向查询结果 =====")
    res_full = mac_api.get_mac_prefixes_by_vendor("vmware")
    print(f"关键词: 'vmware' → 匹配结果: {res_full}")   
    

    print("\n===== 反向模糊查询 厂商名 → MAC前缀】===== ")
    test_keywords = ["vmware", "GIGA-BYTE", "", 123]
    for keyword in test_keywords:
        mac_result = mac_api.get_mac_prefixes_by_vendor(keyword)
        print(f"\n 关键词: '{keyword}' → 匹配结果: \n{mac_result}")   
    