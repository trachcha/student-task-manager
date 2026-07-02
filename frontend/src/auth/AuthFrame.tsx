import type { ReactNode } from "react";

interface AuthFrameProps {
  children: ReactNode;
}

export default function AuthFrame({ children }: AuthFrameProps) {
  return (
    <div className="auth-page">
      <div className="auth-rings">
        <div className="auth-ring auth-ring--4">
          <div className="auth-ring auth-ring--3">
            <div className="auth-ring auth-ring--2">
              <div className="auth-ring auth-ring--1">
                <div className="auth-inner">{children}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
