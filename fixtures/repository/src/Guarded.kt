package demo
import demo.security.RequiresAcl
@RequiresAcl("admin")
class GuardedKotlin {
    @RequiresAcl("read")
    fun read() {}
    fun unguarded() {}
}
