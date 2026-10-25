"""RSA 체험관에서 쓰는 수학 함수 모음.

화면(HTML)과 상관없는 순수 파이썬 코드라서
터미널에서 `python py/rsa_math.py` 로 따로 실행해 볼 수도 있습니다.
"""
import math
import random

SECONDS_PER_YEAR = 365.25 * 24 * 60 * 60
UNIVERSE_AGE_YEARS = 1.38e10  # 우주 나이 약 138억 년


# ── 소수 만들기 ──────────────────────────────────────────

def sieve(limit):
    """limit 이하의 모든 소수 (에라토스테네스의 체)."""
    flags = bytearray([1]) * (limit + 1)
    flags[0:2] = b"\x00\x00"
    for i in range(2, math.isqrt(limit) + 1):
        if flags[i]:
            flags[i * i :: i] = bytes(len(range(i * i, limit + 1, i)))
    return [i for i, flag in enumerate(flags) if flag]


SMALL_PRIMES = sieve(1000)

# 이 값보다 작은 수는 아래 밑(base)들로만 검사해도 결과가 100% 정확하다.
_EXACT_LIMIT = 3_317_044_064_679_887_385_961_981
_EXACT_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)


def is_prime(n, rounds=24):
    """밀러-라빈 소수 판정. 아주 큰 수는 무작위 밑으로 rounds번 검사한다."""
    if n < 2:
        return False
    for p in SMALL_PRIMES:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    if n < _EXACT_LIMIT:
        bases = _EXACT_BASES
    else:
        bases = (random.randrange(2, n - 1) for _ in range(rounds))
    for a in bases:
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def primes_between(lo, hi):
    """lo 이상 hi 이하의 모든 소수."""
    return [p for p in sieve(hi) if p >= lo]


def random_prime(lo, hi):
    """lo 이상 hi 이하의 소수를 무작위로 하나 고른다."""
    while True:
        n = random.randint(lo, hi) | 1
        if n <= hi and is_prime(n):
            return n


def random_semiprime(p_range, q_range=None):
    """서로 다른 두 소수 p < q 와 N = p × q 를 만든다."""
    q_range = q_range or p_range
    p = random_prime(*p_range)
    q = random_prime(*q_range)
    while q == p:
        q = random_prime(*q_range)
    p, q = sorted((p, q))
    return p, q, p * q


# ── 소인수분해: 작은 수부터 하나씩 나눠 보기 ──────────────

BATCH = 128            # 큰 N은 홀수를 이만큼씩 묶어서 검사한다 (find_divisor 설명 참고)
BATCH_MIN_BITS = 1024  # 이보다 작은 N은 하나씩 바로 나누는 쪽이 더 빠르다


def find_divisor(n, start, stop):
    """start부터 stop 직전까지의 홀수로 n을 차례로 나눠 본다.
    나누어떨어지는 첫 수를 돌려주고, 없으면 None.

    RSA-2048, RSA-8192처럼 N이 아주 길면 한 번 나누는 데도 시간이 오래 걸린다.
    그래서 홀수 128개를 모두 곱한 수 P와 N의 최대공약수를 한 번에 구한다.
    최대공약수가 1이면 N과 P에 공통인 약수가 없으니, 128개 중 어느 것도 N을 나누지 못한다.
    1보다 클 때만 그 묶음을 하나씩 나눠 본다. 홀수 하나하나를 모두 확인하는 것은 똑같다."""
    if n.bit_length() < BATCH_MIN_BITS:
        for d in range(start, stop, 2):
            if n % d == 0:
                return d
        return None
    for lo in range(start, stop, 2 * BATCH):
        group = range(lo, min(lo + 2 * BATCH, stop), 2)
        if math.gcd(n, math.prod(group)) > 1:
            for d in group:
                if n % d == 0:
                    return d
    return None


# ── RSA 암호화 / 복호화 ─────────────────────────────────

def choose_e(phi):
    """φ(N)과 서로소인 공개 지수 e를 고른다. (체험용으로 작은 17을 먼저 시도)"""
    for e in (17, 5, 7, 11, 13, 3, 19, 23):
        if e < phi and math.gcd(e, phi) == 1:
            return e
    e = 3
    while math.gcd(e, phi) != 1:
        e += 2
    return e


def private_key(p, q, e):
    """p, q를 알면 φ(N) = (p-1)(q-1) 과 개인키 d = e⁻¹ mod φ(N) 을 구할 수 있다.
    e와 φ(N)이 서로소가 아니면 ValueError."""
    phi = (p - 1) * (q - 1)
    return phi, pow(e, -1, phi)


def generate_keys(prime_range):
    """RSA 키 만들기. 바이트(0~255)를 담을 수 있도록 N > 255 가 되게 하고,
    보는 사람이 헷갈리지 않게 개인키 d가 공개키 e와 같아지는 경우는 다시 만든다."""
    while True:
        p, q, n = random_semiprime(prime_range)
        if n <= 255:
            continue
        e = choose_e((p - 1) * (q - 1))
        _, d = private_key(p, q, e)
        if d != e:
            return {"p": p, "q": q, "n": n, "e": e, "d": d}


def encrypt_text(text, n, e):
    """글자를 UTF-8 바이트(0~255)로 바꾼 뒤, 바이트마다 C = M^e mod N."""
    return [pow(m, e, n) for m in text.encode("utf-8")]


def decrypt_numbers(cipher, n, d):
    """숫자마다 M = C^d mod N."""
    return [pow(c, d, n) for c in cipher]


def bytes_to_text(values):
    """복호화한 숫자들을 다시 글자로. 0~255 밖의 값이 있으면 None."""
    if any(v > 255 for v in values):
        return None
    return bytes(values).decode("utf-8", errors="replace")


if __name__ == "__main__":
    p, q, n = random_semiprime((101, 997))
    print(f"{n:,} = {p} × {q}  (하나씩 나눠서 찾은 인수: {find_divisor(n, 3, math.isqrt(n) + 1)})")

    keys = generate_keys((11, 97))
    secret = encrypt_text("안녕, RSA!", keys["n"], keys["e"])
    print(f"공개키 N={keys['n']}, e={keys['e']} / 개인키 d={keys['d']}")
    print("암호문:", secret)
    print("해독:", bytes_to_text(decrypt_numbers(secret, keys["n"], keys["d"])))
