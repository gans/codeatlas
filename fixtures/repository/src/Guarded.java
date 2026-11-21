package demo;
import demo.security.RequiresAcl;
@RequiresAcl("admin")
public class Guarded {
    @RequiresAcl("read")
    public void read() {}
    public void unguarded() {}
}
