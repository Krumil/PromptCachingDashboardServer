from datetime import datetime
from typing import Dict, List, Set
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class CacheStats:
    total_prime_cached: float
    prime_withdrawals: float
    net_prime_cached: float
    unique_cachers: int
    wtd_avg_days_cached: float
    wtd_avg_days_cached_with_extensions: float
    monthly_stats: Dict[str, float]
    cumulative_stats: Dict[str, float]
    new_cachers_monthly: Dict[str, int]
    prime_unlocks_monthly: Dict[str, float]

class StatsService:
    def __init__(self):
        self.cache_stats = None

    def _calculate_monthly_stats(self, rows: List[Dict]) -> Dict[str, float]:
        """Calculate monthly $PRIME cached amounts"""
        monthly_stats = defaultdict(float)
        for row in rows:
            deposit_date = row.get('deposited')
            if deposit_date:
                month_key = deposit_date.strftime('%Y-%m')
                monthly_stats[month_key] += float(row.get('norm_amt', 0))
        return dict(monthly_stats)

    def _calculate_cumulative_stats(self, monthly_stats: Dict[str, float]) -> Dict[str, float]:
        """Calculate cumulative $PRIME cached over time"""
        cumulative = defaultdict(float)
        running_total = 0
        for month in sorted(monthly_stats.keys()):
            running_total += monthly_stats[month]
            cumulative[month] = running_total
        return dict(cumulative)

    def _calculate_new_cachers_monthly(self, rows: List[Dict]) -> Dict[str, int]:
        """Calculate new unique cachers per month"""
        monthly_new_cachers = defaultdict(set)
        for row in rows:
            deposit_date = row.get('deposited')
            user = row.get('user')
            if deposit_date and user:
                month_key = deposit_date.strftime('%Y-%m')
                monthly_new_cachers[month_key].add(user)
        
        return {k: len(v) for k, v in monthly_new_cachers.items()}

    def _calculate_prime_unlocks(self, rows: List[Dict]) -> Dict[str, float]:
        """Calculate $PRIME unlocks by month"""
        monthly_unlocks = defaultdict(float)
        for row in rows:
            unlock_date = row.get('old_unlock')
            if unlock_date:
                month_key = unlock_date.strftime('%Y-%m')
                monthly_unlocks[month_key] += float(row.get('norm_amt', 0))
        return dict(monthly_unlocks)

    def calculate_stats(self, dune_rows: List[Dict]) -> CacheStats:
        """Calculate all caching statistics from Dune query results"""
        if not dune_rows:
            return None

        # Calculate basic stats
        total_prime = sum(float(row.get('norm_amt', 0)) for row in dune_rows)
        withdrawals = 0  # TODO: Add withdrawal calculation when available
        net_prime = total_prime - withdrawals
        
        # Calculate unique cachers
        unique_cachers = len({row.get('user') for row in dune_rows if row.get('user')})

        # Calculate weighted average days
        total_weighted_days = 0
        total_weighted_days_extended = 0
        total_weight = 0

        for row in dune_rows:
            amount = float(row.get('norm_amt', 0))
            old_duration = float(row.get('old_duration', 0))
            new_duration = float(row.get('new_duration', 0))
            
            total_weighted_days += amount * old_duration
            total_weighted_days_extended += amount * new_duration
            total_weight += amount

        wtd_avg_days = total_weighted_days / total_weight if total_weight > 0 else 0
        wtd_avg_days_extended = total_weighted_days_extended / total_weight if total_weight > 0 else 0

        # Calculate time-based stats
        monthly_stats = self._calculate_monthly_stats(dune_rows)
        cumulative_stats = self._calculate_cumulative_stats(monthly_stats)
        new_cachers_monthly = self._calculate_new_cachers_monthly(dune_rows)
        prime_unlocks_monthly = self._calculate_prime_unlocks(dune_rows)

        self.cache_stats = CacheStats(
            total_prime_cached=total_prime,
            prime_withdrawals=withdrawals,
            net_prime_cached=net_prime,
            unique_cachers=unique_cachers,
            wtd_avg_days_cached=wtd_avg_days,
            wtd_avg_days_cached_with_extensions=wtd_avg_days_extended,
            monthly_stats=monthly_stats,
            cumulative_stats=cumulative_stats,
            new_cachers_monthly=new_cachers_monthly,
            prime_unlocks_monthly=prime_unlocks_monthly
        )

        return self.cache_stats

# Create a singleton instance
stats_service = StatsService() 