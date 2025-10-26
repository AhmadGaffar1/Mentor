# Async Migration Guide

## 📊 Performance Improvements

### Before (Synchronous)
```
Discovery: Serper (3s) → Tavily (3s) = 6s total
Extraction: 10 URLs × 5s each = 50s total
TOTAL: ~56 seconds
```

### After (Asynchronous)
```
Discovery: max(Serper, Tavily) = 3s total (concurrent)
Extraction: 10 URLs in parallel = ~5s total
TOTAL: ~8 seconds (7x faster!)
```

---

## 🔄 Key Changes

### 1. **HTTP Client: `requests` → `aiohttp`**
```python
# Before (blocking)
response = requests.post(url, json=payload)
data = response.json()

# After (non-blocking)
async with aiohttp.ClientSession() as session:
    async with session.post(url, json=payload) as response:
        data = await response.json()
```

### 2. **File I/O: `open()` → `aiofiles`**
```python
# Before (blocking)
with open(file_path, "rb") as f:
    data = f.read()

# After (non-blocking)
async with aiofiles.open(file_path, "rb") as f:
    data = await f.read()
```

### 3. **Sleep: `time.sleep()` → `asyncio.sleep()`**
```python
# Before (blocks entire thread)
time.sleep(5)

# After (yields control to event loop)
await asyncio.sleep(5)
```

### 4. **Concurrent Execution**
```python
# Before (sequential)
for item in items:
    result = process_item(item)
    time.sleep(5)  # Artificial delay

# After (parallel)
tasks = [process_item(item) for item in items]
results = await asyncio.gather(*tasks)
```

---

## 📦 New Dependencies

Add to your `requirements.txt`:
```
aiohttp==3.9.1
aiofiles==23.2.1
```

Install:
```bash
pip install aiohttp aiofiles
```

---

## 🚀 Usage Examples

### Basic Usage
```python
import asyncio
from uuid import uuid4
from APP.Services.Search import searching_Serper_Tavily_YouTube_AssemblyAI

async def main():
    # Text search
    results = await searching_Serper_Tavily_YouTube_AssemblyAI(
        id=uuid4(),
        query="machine learning basics",
        search_type="search"
    )
    
    print(f"Found {len(results)} articles")
    for item in results:
        print(f"- {item['title']}")
        print(f"  Text length: {len(item.get('text', ''))}")

# Run the async function
asyncio.run(main())
```

### Video Search
```python
async def search_videos():
    results = await searching_Serper_Tavily_YouTube_AssemblyAI(
        id=uuid4(),
        query="python tutorial for beginners",
        search_type="videos"
    )
    
    for video in results:
        print(f"📹 {video['title']}")
        print(f"   Channel: {video['channel']}")
        print(f"   Duration: {video['duration']}")
        print(f"   Transcript: {video['transcript_source']}")

asyncio.run(search_videos())
```

### Integration with Web Framework (FastAPI)
```python
from fastapi import FastAPI
from uuid import uuid4

app = FastAPI()

@app.get("/search")
async def search_endpoint(query: str, type: str = "search"):
    """
    Async endpoint - no blocking!
    FastAPI natively supports async/await.
    """
    results = await searching_Serper_Tavily_YouTube_AssemblyAI(
        id=uuid4(),
        query=query,
        search_type=type
    )
    return {"results": results, "count": len(results)}
```

### Integration with Django (Async Views)
```python
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from uuid import uuid4

async def search_view(request):
    """
    Django 3.1+ supports async views with ASGI.
    """
    query = request.GET.get("query", "")
    search_type = request.GET.get("type", "search")
    
    results = await searching_Serper_Tavily_YouTube_AssemblyAI(
        id=uuid4(),
        query=query,
        search_type=search_type
    )
    
    return JsonResponse({"results": results})
```

---

## ⚠️ Common Pitfalls

### 1. **Forgetting `await`**
```python
# ❌ Wrong - returns coroutine object, doesn't execute
result = discover_with_serper(id, query)

# ✅ Correct - actually executes the function
result = await discover_with_serper(id, query)
```

### 2. **Mixing Sync and Async Code**
```python
# ❌ Wrong - time.sleep blocks event loop
async def bad_function():
    await some_async_call()
    time.sleep(5)  # Blocks everything!

# ✅ Correct - use asyncio.sleep
async def good_function():
    await some_async_call()
    await asyncio.sleep(5)  # Non-blocking
```

### 3. **Not Using `asyncio.run()`**
```python
# ❌ Wrong - can't call async function directly
result = searching_Serper_Tavily_YouTube_AssemblyAI(id, query)

# ✅ Correct - use asyncio.run() in scripts
result = asyncio.run(
    searching_Serper_Tavily_YouTube_AssemblyAI(id, query)
)
```

### 4. **Blocking Operations in Async Functions**
```python
# ❌ Wrong - pytube is synchronous, blocks event loop
async def bad_download():
    yt = YouTube(url)
    stream = yt.streams.first()
    stream.download()  # Blocks!

# ✅ Correct - run in thread pool executor
async def good_download():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_download)
```

---

## 🎯 Best Practices

### 1. **Use `asyncio.gather()` for Parallel Tasks**
```python
# Process multiple queries concurrently
queries = ["ML basics", "Python tutorial", "Data Science"]

tasks = [
    searching_Serper_Tavily_YouTube_AssemblyAI(uuid4(), q)
    for q in queries
]

all_results = await asyncio.gather(*tasks)
```

### 2. **Handle Exceptions Gracefully**
```python
# Prevent one failure from stopping everything
results = await asyncio.gather(
    *tasks,
    return_exceptions=True  # Returns exceptions instead of raising
)

# Filter out failures
successful = [r for r in results if not isinstance(r, Exception)]
failed = [r for r in results if isinstance(r, Exception)]
```

### 3. **Use Timeouts to Prevent Hanging**
```python
try:
    result = await asyncio.wait_for(
        some_long_operation(),
        timeout=30.0  # 30 seconds max
    )
except asyncio.TimeoutError:
    print("Operation timed out")
```

### 4. **Rate Limiting with Semaphores**
```python
# Limit concurrent API calls
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

async def rate_limited_task(item):
    async with semaphore:
        return await process_item(item)

tasks = [rate_limited_task(item) for item in items]
results = await asyncio.gather(*tasks)
```

---

## 📈 Performance Monitoring

### Measure Execution Time
```python
import time

async def benchmark():
    start = time.time()
    
    results = await searching_Serper_Tavily_YouTube_AssemblyAI(
        id=uuid4(),
        query="async python tutorial",
        search_type="search"
    )
    
    elapsed = time.time() - start
    print(f"Completed in {elapsed:.2f} seconds")
    print(f"Processed {len(results)} items")
    print(f"Average: {elapsed/len(results):.2f}s per item")

asyncio.run(benchmark())
```

---

## 🔍 Debugging Async Code

### Enable Debug Mode
```python
import asyncio
import logging

# Enable asyncio debug mode
asyncio.run(main(), debug=True)

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
```

### Track Pending Tasks
```python
async def debug_info():
    tasks = asyncio.all_tasks()
    print(f"Active tasks: {len(tasks)}")
    for task in tasks:
        print(f"  - {task.get_name()}: {task}")
```

---

## 🧪 Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_search():
    results = await searching_Serper_Tavily_YouTube_AssemblyAI(
        id=uuid4(),
        query="test query",
        search_type="search"
    )
    
    assert len(results) > 0
    assert results[0].get("title")
    assert results[0].get("text")
```

---

## 📚 Additional Resources

- [Python Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [FastAPI Async Guide](https://fastapi.tiangolo.com/async/)

---

## 🎓 Summary

**Key Benefits:**
- ✅ **7x faster** for typical workloads
- ✅ **Non-blocking I/O** - better resource utilization
- ✅ **Concurrent API calls** - parallel processing
- ✅ **Scalable** - handles more requests with same resources

**Migration Checklist:**
- [ ] Install `aiohttp` and `aiofiles`
- [ ] Add `async` keyword to function definitions
- [ ] Add `await` keyword before async calls
- [ ] Replace `requests` with `aiohttp`
- [ ] Replace `time.sleep()` with `asyncio.sleep()`
- [ ] Use `asyncio